from flask import Flask, request, jsonify, g
from flask_cors import CORS
import serpapi
import psycopg2
from psycopg2 import sql
import os
import re
import json
import hmac
import jwt
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlsplit, unquote
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ---------------------------------------------------------------------------
# CORS
# O site e a API ficam no mesmo domínio da Vercel (o front chama "/api/..."),
# então o navegador nem precisa de CORS. Deixamos liberado só para o domínio
# do projeto (e para outros que você listar em ALLOWED_ORIGINS, separados por
# vírgula — útil para testar em http://localhost:5000, por exemplo).
# ---------------------------------------------------------------------------
ORIGENS_PERMITIDAS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "https://comparaiweb.vercel.app").split(",")
    if o.strip()
]
CORS(app, resources={r"/api/*": {"origins": ORIGENS_PERMITIDAS}})

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------

# Limite de tentativas de login por senha
MAX_TENTATIVAS = 5
BLOQUEIO_MINUTOS = 15

# Token de login (JWT). JWT_SECRET deve ser uma string longa e aleatória,
# configurada nas variáveis de ambiente da Vercel.
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_DIAS = 7

# Proteção da cota da SerpAPI
CACHE_HORAS = 6                                                        # quanto tempo uma busca fica guardada
LIMITE_BUSCA_POR_MINUTO = int(os.environ.get("LIMITE_BUSCA_POR_MINUTO", "8"))   # buscas novas por IP/minuto
LIMITE_SERPAPI_POR_DIA = int(os.environ.get("LIMITE_SERPAPI_POR_DIA", "100"))   # buscas novas no site todo/dia

# Regras de validação (o front-end repete essas regras só para dar resposta rápida;
# quem vale de verdade é o servidor)
EMAIL_RE = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")
SENHA_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{6,128}$")
NOME_MAX = 50

TABELAS = ("usuario", "favorito", "cache_busca", "limite_uso")

# Hash "de mentira" usado para o login demorar o mesmo tempo quando o e-mail
# não existe (evita descobrir quais e-mails têm conta pelo tempo de resposta)
HASH_FALSO = generate_password_hash("senha-falsa-para-igualar-o-tempo")


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def texto(valor):
    """Devolve o valor como string sem espaços nas pontas (ou '' se não for texto)."""
    return valor.strip() if isinstance(valor, str) else ""


def normalizar_email(valor):
    return texto(valor).lower()


def limpar_url(valor, tamanho_max):
    """Aceita só links http(s) de tamanho razoável. Qualquer outra coisa vira None."""
    valor = texto(valor)
    if not valor or len(valor) > tamanho_max:
        return None
    try:
        partes = urlsplit(valor)
    except ValueError:
        return None
    if partes.scheme not in ("http", "https") or not partes.netloc:
        return None
    return valor


def ip_do_cliente():
    # Na Vercel o IP real vem nesses cabeçalhos (a própria Vercel os define)
    ip = request.headers.get("x-vercel-forwarded-for") or request.headers.get("x-forwarded-for") or ""
    ip = ip.split(",")[0].strip()
    return ip or request.remote_addr or "desconhecido"


def gerar_token(email):
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET não configurada")

    agora = datetime.now(timezone.utc)
    payload = {
        "email": email,
        "iat": agora,
        "exp": agora + timedelta(days=JWT_DIAS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def resposta_bloqueio(segundos):
    """Resposta 429 usada quando a conta está bloqueada por excesso de tentativas."""
    segundos = int(segundos)
    minutos = (segundos + 59) // 60
    return jsonify({
        "autenticado": False,
        "erro": f"Muitas tentativas. Tente novamente em {minutos} min.",
        "segundos_restantes": segundos
    }), 429


def exigir_login(f):
    """
    Decorator: só deixa a rota executar se a requisição trouxer um token
    válido no header 'Authorization: Bearer <token>'. O e-mail do usuário
    logado fica disponível em g.email.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not JWT_SECRET:
            return jsonify({"erro": "JWT_SECRET não configurada"}), 500

        cabecalho = request.headers.get("Authorization", "")
        if not cabecalho.startswith("Bearer "):
            return jsonify({"erro": "Login necessário"}), 401

        try:
            dados = jwt.decode(
                cabecalho[7:], JWT_SECRET, algorithms=["HS256"],
                options={"require": ["exp", "email"]}
            )
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Sessão inválida ou expirada. Faça login novamente."}), 401

        g.email = dados["email"]
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

def get_conn():
    """
    Abre uma conexão nova com o Postgres a cada chamada.
    Em ambiente serverless (Vercel) não dá pra manter uma conexão
    global viva entre execuções — por isso abrimos e fechamos
    a conexão dentro de cada request.
    """
    # Tenta primeiro uma connection string completa (geralmente aponta
    # para o pooler, que funciona por IPv4 - ao contrário do host direto,
    # que é IPv6-only e falha em ambiente serverless da Vercel).
    # Fazemos o parsing manualmente com urllib em vez de deixar o
    # psycopg2 interpretar a string inteira, pra evitar erros com
    # parâmetros de query mal formados.
    connection_string = (
        os.environ.get("DATABASE_POSTGRES_URL")
        or os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
    )

    if connection_string:
        parsed = urlsplit(connection_string)

        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            dbname=(parsed.path.lstrip("/") or "postgres"),
            user=parsed.username,
            password=unquote(parsed.password) if parsed.password else None,
            sslmode="require",
            connect_timeout=10,
        )

    # Se não tiver nenhuma connection string, cai para as variáveis
    # separadas (atenção: DATABASE_POSTGRES_HOST costuma ser o host
    # direto/IPv6-only, então isso só deve funcionar fora da Vercel).
    host = os.environ.get("DATABASE_POSTGRES_HOST")
    user = os.environ.get("DATABASE_POSTGRES_USER")
    password = os.environ.get("DATABASE_POSTGRES_PASSWORD")
    dbname = os.environ.get("DATABASE_POSTGRES_DATABASE")
    port = os.environ.get("DATABASE_POSTGRES_PORT", "5432")

    if host and user and password and dbname:
        return psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",
            connect_timeout=10,
        )

    raise RuntimeError(
        "Nenhuma variável de conexão com o banco encontrada "
        "(DATABASE_POSTGRES_URL / DATABASE_URL / POSTGRES_URL ou "
        "DATABASE_POSTGRES_HOST/USER/PASSWORD/DATABASE)"
    )


@contextmanager
def banco():
    """
    Uso:   with banco() as cur:
               cur.execute(...)

    Abre a conexão, entrega o cursor, faz commit se tudo der certo,
    rollback se der erro e SEMPRE fecha a conexão no final.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def criar_tabelas_se_nao_existirem():
    """
    Cria as tabelas na primeira execução. A versão completa (com os ALTER TABLE
    para bancos antigos) está em Back-end/schema.sql.
    Também liga o RLS (Row Level Security) em todas as tabelas, para elas não
    ficarem expostas pela API pública do Supabase.
    """
    with banco() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario SERIAL PRIMARY KEY,
            nome VARCHAR(50),
            gmail VARCHAR(250),
            senha VARCHAR(255),
            foto VARCHAR(500),
            tentativas_falhas INTEGER NOT NULL DEFAULT 0,
            bloqueado_ate TIMESTAMPTZ
        )
        """)

        # impede duas contas com o mesmo e-mail, seja criada por senha ou por Google
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usuario_gmail_unico ON usuario (gmail)")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS favorito (
            id_favorito SERIAL PRIMARY KEY,
            gmail_usuario VARCHAR(250),
            titulo VARCHAR(300),
            imagem VARCHAR(500),
            preco VARCHAR(50),
            loja VARCHAR(100),
            link VARCHAR(500)
        )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_favorito_gmail ON favorito (gmail_usuario)")

        # buscas já feitas (evita gastar a cota da SerpAPI com a mesma pesquisa)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cache_busca (
            chave VARCHAR(200) PRIMARY KEY,
            resultado TEXT NOT NULL,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)

        # contadores do limite de buscas (por IP/minuto e total/dia)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS limite_uso (
            chave VARCHAR(100) NOT NULL,
            janela TIMESTAMPTZ NOT NULL,
            total INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (chave, janela)
        )
        """)

        # Liga o RLS só nas tabelas que ainda não têm (consulta barata, sem travar nada)
        cur.execute("""
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND c.relname::text = ANY(%s)
          AND NOT c.relrowsecurity
        """, (list(TABELAS),))
        for (nome_tabela,) in cur.fetchall():
            cur.execute(
                sql.SQL("ALTER TABLE public.{} ENABLE ROW LEVEL SECURITY").format(
                    sql.Identifier(nome_tabela)
                )
            )


def buscar_ou_criar_usuario(email, nome, foto, criar=False):
    with banco() as cur:
        cur.execute(
            "SELECT nome, gmail FROM usuario WHERE lower(gmail) = %s LIMIT 1",
            (email,)
        )
        resultado = cur.fetchone()

        if resultado:
            # já existe: atualiza a foto (pode ter mudado no Google) e retorna
            cur.execute(
                "UPDATE usuario SET foto = %s WHERE lower(gmail) = %s",
                (foto, email)
            )
            return {"nome": resultado[0], "email": resultado[1], "foto": foto}

        # não existe: só cria se a chamada veio da página de criar conta
        if not criar:
            return None

        # cria um novo usuário (sem senha, já que é login via Google).
        # ON CONFLICT cobre o caso raro de dois cliques ao mesmo tempo.
        cur.execute(
            """
            INSERT INTO usuario (nome, gmail, foto) VALUES (%s, %s, %s)
            ON CONFLICT (gmail) DO NOTHING
            """,
            (nome, email, foto)
        )
        return {"nome": nome, "email": email, "foto": foto}


# Garante que as tabelas existem quando a API sobe
try:
    criar_tabelas_se_nao_existirem()
except Exception as e:
    print("Falha ao criar tabelas:", e)


# ---------------------------------------------------------------------------
# Busca de produtos (SerpAPI) com cache e limite de uso
# ---------------------------------------------------------------------------

def item_para_json(item):
    return {
        "imagem": item.get("thumbnail"),
        "posicao": item.get("position"),
        "Icon_loja": item.get("source_icon"),
        "title": item.get("title"),
        "nota": item.get("rating"),
        "compras": item.get("reviews"),   # número de avaliações
        "preco": item.get("price"),
        "loja": item.get("source"),
        "link": item.get("product_link")
    }


def buscar_no_serpapi(termo):
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY não configurada")

    client = serpapi.Client(api_key=api_key)
    results = client.search({
        "engine": "google_shopping",
        "q": termo,
        "location": "Brazil",
        "hl": "pt-br",
        "gl": "br"
    })
    return [item_para_json(item) for item in results.get("shopping_results", [])]


def consumir_limite(cur, chave, unidade, limite):
    """
    Soma 1 no contador (chave, janela de tempo) e diz se ainda está dentro do limite.
    unidade = 'minute' ou 'day'.
    """
    cur.execute(
        """
        INSERT INTO limite_uso (chave, janela, total)
        VALUES (%s, date_trunc(%s, NOW()), 1)
        ON CONFLICT (chave, janela) DO UPDATE SET total = limite_uso.total + 1
        RETURNING total
        """,
        (chave, unidade)
    )
    total = cur.fetchone()[0]

    # limpeza de contadores velhos, só de vez em quando (quando a janela é nova)
    if total == 1:
        cur.execute("DELETE FROM limite_uso WHERE janela < NOW() - INTERVAL '2 days'")

    return total <= limite


def buscar_com_cache(termo):
    """
    Devolve (lista, None) em caso de sucesso ou (None, (mensagem, status)) em caso de erro.

    Ordem: 1) cache  ->  2) limites de uso  ->  3) SerpAPI  ->  4) guarda no cache.
    Se o banco falhar nos passos de cache/limite, a busca continua funcionando
    (só sem a proteção), para o site não cair por causa disso.
    """
    chave = " ".join(termo.lower().split())[:200]

    try:
        with banco() as cur:
            cur.execute(
                """
                SELECT resultado FROM cache_busca
                WHERE chave = %s AND criado_em > NOW() - %s * INTERVAL '1 hour'
                """,
                (chave, CACHE_HORAS)
            )
            linha = cur.fetchone()
            if linha:
                return json.loads(linha[0]), None

            if not consumir_limite(cur, "ip:" + ip_do_cliente(), "minute", LIMITE_BUSCA_POR_MINUTO):
                return None, ("Muitas buscas seguidas. Aguarde um minuto e tente de novo.", 429)

            if not consumir_limite(cur, "total", "day", LIMITE_SERPAPI_POR_DIA):
                return None, ("O limite de buscas de hoje foi atingido. Tente novamente amanhã.", 429)
    except Exception as e:
        print("Falha no cache/limite de busca:", e)

    try:
        lista = buscar_no_serpapi(termo)
    except RuntimeError as e:
        print(e)
        return None, ("Busca indisponível no momento.", 500)
    except Exception as e:
        print("Erro na SerpAPI:", e)
        return None, ("Não foi possível buscar produtos agora. Tente novamente.", 502)

    if lista:
        try:
            with banco() as cur:
                cur.execute(
                    """
                    INSERT INTO cache_busca (chave, resultado) VALUES (%s, %s)
                    ON CONFLICT (chave) DO UPDATE
                    SET resultado = EXCLUDED.resultado, criado_em = NOW()
                    """,
                    (chave, json.dumps(lista))
                )
                cur.execute("DELETE FROM cache_busca WHERE criado_em < NOW() - INTERVAL '7 days'")
        except Exception as e:
            print("Falha ao guardar o cache:", e)

    return lista, None


@app.route('/api/produtos', methods=['POST'])
def lista_produtos():
    info = request.get_json(silent=True) or {}
    produto = texto(info.get('nomeProduto'))

    if not produto:
        return jsonify({"erro": "nomeProduto não informado"}), 400

    if len(produto) < 2 or len(produto) > 100:
        return jsonify({"erro": "O nome do produto deve ter entre 2 e 100 caracteres"}), 400

    lista, erro = buscar_com_cache(produto)
    if erro:
        return jsonify({"erro": erro[0]}), erro[1]

    return jsonify(lista)


@app.route('/api/categoria', methods=['POST'])
def categoria():
    lista, erro = buscar_com_cache("eletronicos")
    if erro:
        return jsonify({"erro": erro[0]}), erro[1]

    return jsonify(lista)


# ---------------------------------------------------------------------------
# Usuários e login
# ---------------------------------------------------------------------------

@app.route('/api/usuarios', methods=['POST'])
def users():
    info_users = request.get_json(silent=True) or {}

    nome = texto(info_users.get("nome"))
    gmail = normalizar_email(info_users.get("email"))
    senha = info_users.get("senha") if isinstance(info_users.get("senha"), str) else ""

    if not nome or not gmail or not senha:
        return jsonify({"erro": "nome, email e senha são obrigatórios"}), 400

    if len(nome) > NOME_MAX or "<" in nome or ">" in nome:
        return jsonify({"erro": f"Nome inválido (máximo {NOME_MAX} caracteres, sem < ou >)."}), 400

    if len(gmail) > 250 or not EMAIL_RE.match(gmail):
        return jsonify({"erro": "E-mail inválido."}), 400

    if not SENHA_RE.match(senha):
        return jsonify({
            "erro": "A senha deve ter de 6 a 128 caracteres, com letras, números e caracteres especiais."
        }), 400

    try:
        with banco() as cur:
            cur.execute("SELECT 1 FROM usuario WHERE lower(gmail) = %s LIMIT 1", (gmail,))
            if cur.fetchone():
                return jsonify({"erro": "Já existe uma conta com esse e-mail."}), 409

            cur.execute(
                "INSERT INTO usuario (nome, gmail, senha) VALUES (%s, %s, %s)",
                (nome, gmail, generate_password_hash(senha))
            )
    except psycopg2.IntegrityError:
        # dois cadastros ao mesmo tempo com o mesmo e-mail
        return jsonify({"erro": "Já existe uma conta com esse e-mail."}), 409

    # já devolve o token: quem acabou de criar a conta fica logado
    return jsonify({
        "mensagem": "Usuário cadastrado com sucesso",
        "nome": nome,
        "email": gmail,
        "token": gerar_token(gmail)
    }), 201


@app.route('/api/login-google', methods=['POST'])
def login_google():
    dados = request.get_json(silent=True) or {}
    token = dados.get('token')
    # só cria conta nova se o front-end pedir explicitamente (página de criar conta)
    criar = dados.get('criar') is True

    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    if not client_id:
        # sem o client_id a biblioteca NÃO confere de qual app o token é,
        # então preferimos recusar a aceitar um token de qualquer app
        return jsonify({"erro": "GOOGLE_CLIENT_ID não configurada"}), 500

    if not token or not isinstance(token, str):
        return jsonify({"erro": "token não informado"}), 400

    try:
        info = id_token.verify_oauth2_token(token, grequests.Request(), client_id)
    except ValueError:
        return jsonify({"erro": "token inválido"}), 401
    except Exception as e:
        print("Erro ao validar token do Google:", e)
        return jsonify({"erro": "Não foi possível validar o login com o Google agora."}), 502

    if not info.get('email') or not info.get('email_verified'):
        return jsonify({"erro": "E-mail do Google não verificado"}), 401

    email = normalizar_email(info['email'])
    nome = (texto(info.get('name')) or email.split('@')[0])[:NOME_MAX]
    foto = limpar_url(info.get('picture'), 500)

    usuario = buscar_ou_criar_usuario(email, nome, foto, criar)

    if usuario is None:
        return jsonify({
            "erro": "Não existe uma conta com esse e-mail. Crie uma conta primeiro."
        }), 404

    # o token usa o e-mail como está salvo no banco
    usuario["token"] = gerar_token(usuario["email"])
    return jsonify(usuario)


@app.route('/api/login', methods=['POST'])
def login():
    login_json = request.get_json(silent=True) or {}

    email_user = normalizar_email(login_json.get("email"))
    senha_user = login_json.get("senha") if isinstance(login_json.get("senha"), str) else ""

    if not email_user or not senha_user:
        return jsonify({"erro": "email e senha são obrigatórios"}), 400

    if len(senha_user) > 128:
        # evita gastar processamento fazendo hash de textos gigantes
        return jsonify({"autenticado": False, "erro": "E-mail ou senha incorretos."}), 401

    erro_generico = (jsonify({"autenticado": False, "erro": "E-mail ou senha incorretos."}), 401)

    with banco() as cur:
        # O cálculo do bloqueio é feito no próprio banco (NOW()),
        # assim não há problema de fuso horário entre Python e Postgres
        cur.execute(
            """
            SELECT nome, gmail, senha, foto,
                   CASE WHEN bloqueado_ate > NOW()
                        THEN CEIL(EXTRACT(EPOCH FROM (bloqueado_ate - NOW())))
                        ELSE 0 END
            FROM usuario
            WHERE lower(gmail) = %s
            LIMIT 1
            """,
            (email_user,)
        )
        resultado = cur.fetchone()

        if not resultado or resultado[2] is None:
            # e-mail não existe OU conta criada só via Google (nunca teve senha):
            # mesma resposta e mesmo tempo de espera nos dois casos
            check_password_hash(HASH_FALSO, senha_user)
            return erro_generico

        nome_login, gmail_login, senha_db, foto_login, segundos_bloqueio = resultado

        # 1) Conta bloqueada? Recusa mesmo que a senha esteja certa
        if segundos_bloqueio > 0:
            return resposta_bloqueio(segundos_bloqueio)

        # 2) Confere a senha. Aceita o hash novo e também contas antigas
        # com senha em texto puro (que são convertidas para hash no login).
        senha_ok = False
        precisa_migrar = False

        if senha_db.startswith(("scrypt:", "pbkdf2:")):
            senha_ok = check_password_hash(senha_db, senha_user)
        elif hmac.compare_digest(senha_db.encode(), senha_user.encode()):
            senha_ok = True
            precisa_migrar = True

        # Senha correta: zera o contador (e converte para hash, se ainda era texto puro)
        if senha_ok:
            novo_valor = generate_password_hash(senha_user) if precisa_migrar else senha_db
            cur.execute(
                """
                UPDATE usuario
                SET senha = %s, tentativas_falhas = 0, bloqueado_ate = NULL
                WHERE gmail = %s
                """,
                (novo_valor, gmail_login)
            )

            return jsonify({
                "autenticado": True,
                "usuario": nome_login,
                "nome": nome_login,
                "email": gmail_login,
                "foto": foto_login,
                "token": gerar_token(gmail_login)
            })

        # 3) Senha errada: incrementa; ao atingir o limite, bloqueia e zera o contador
        cur.execute(
            """
            UPDATE usuario
            SET bloqueado_ate = CASE
                    WHEN tentativas_falhas + 1 >= %s
                    THEN NOW() + %s * INTERVAL '1 minute'
                    ELSE bloqueado_ate
                END,
                tentativas_falhas = CASE
                    WHEN tentativas_falhas + 1 >= %s THEN 0
                    ELSE tentativas_falhas + 1
                END
            WHERE gmail = %s
            RETURNING CASE WHEN bloqueado_ate > NOW()
                           THEN CEIL(EXTRACT(EPOCH FROM (bloqueado_ate - NOW())))
                           ELSE 0 END
            """,
            (MAX_TENTATIVAS, BLOQUEIO_MINUTOS, MAX_TENTATIVAS, gmail_login)
        )
        segundos_restantes = cur.fetchone()[0]

        # Se esta tentativa atingiu o limite, já avisa o bloqueio (e a contagem)
        if segundos_restantes > 0:
            return resposta_bloqueio(segundos_restantes)

        return erro_generico


# ---------------------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------------------

@app.route('/api/favoritos/adicionar', methods=['POST'])
@exigir_login
def adicionar_favorito():
    info = request.get_json(silent=True) or {}

    # o e-mail vem do token, não do corpo da requisição
    gmail = g.email

    # os tamanhos batem com as colunas do banco (senão o Postgres dá erro)
    titulo = texto(info.get('titulo'))[:300]
    imagem = limpar_url(info.get('imagem'), 500)
    preco = texto(info.get('preco'))[:50]
    loja = texto(info.get('loja'))[:100]
    link = limpar_url(info.get('link'), 500)

    if not titulo:
        return jsonify({"erro": "titulo é obrigatório"}), 400

    with banco() as cur:
        # o token vale por 7 dias; se a conta foi excluída nesse meio tempo, recusa
        cur.execute("SELECT 1 FROM usuario WHERE gmail = %s", (gmail,))
        if not cur.fetchone():
            return jsonify({"erro": "Conta não encontrada. Faça login novamente."}), 401

        # não deixa favoritar o mesmo produto (mesmo título e loja) duas vezes
        cur.execute(
            """
            INSERT INTO favorito (gmail_usuario, titulo, imagem, preco, loja, link)
            SELECT %s, %s, %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM favorito
                WHERE gmail_usuario = %s AND titulo = %s AND COALESCE(loja, '') = %s
            )
            """,
            (gmail, titulo, imagem, preco, loja, link, gmail, titulo, loja)
        )
        if cur.rowcount == 0:
            return jsonify({"mensagem": "Esse produto já estava nos seus favoritos"}), 200

    return jsonify({"mensagem": "Favorito adicionado com sucesso"}), 201


@app.route('/api/favoritos/listar', methods=['POST'])
@exigir_login
def listar_favoritos():
    with banco() as cur:
        cur.execute(
            """
            SELECT id_favorito, titulo, imagem, preco, loja, link
            FROM favorito
            WHERE gmail_usuario = %s
            ORDER BY id_favorito DESC
            """,
            (g.email,)
        )
        resultados = cur.fetchall()

    return jsonify([
        {
            "id_favorito": linha[0],
            "titulo": linha[1],
            "imagem": linha[2],
            "preco": linha[3],
            "loja": linha[4],
            "link": linha[5]
        }
        for linha in resultados
    ])


@app.route('/api/favoritos/remover', methods=['POST'])
@exigir_login
def remover_favorito():
    info = request.get_json(silent=True) or {}

    try:
        id_favorito = int(info.get('id_favorito'))
    except (TypeError, ValueError):
        return jsonify({"erro": "id_favorito é obrigatório"}), 400

    with banco() as cur:
        cur.execute(
            "DELETE FROM favorito WHERE id_favorito = %s AND gmail_usuario = %s",
            (id_favorito, g.email)
        )

    return jsonify({"mensagem": "Favorito removido com sucesso"})


@app.route('/api/usuarios/atualizar-nome', methods=['POST'])
@exigir_login
def atualizar_nome():
    info = request.get_json(silent=True) or {}
    novo_nome = texto(info.get('nome'))

    if not novo_nome:
        return jsonify({"erro": "nome é obrigatório"}), 400

    if len(novo_nome) > NOME_MAX or "<" in novo_nome or ">" in novo_nome:
        return jsonify({"erro": f"Nome inválido (máximo {NOME_MAX} caracteres, sem < ou >)."}), 400

    with banco() as cur:
        cur.execute("UPDATE usuario SET nome = %s WHERE gmail = %s", (novo_nome, g.email))
        if cur.rowcount == 0:
            return jsonify({"erro": "Conta não encontrada. Faça login novamente."}), 401

    return jsonify({"mensagem": "Nome atualizado com sucesso", "nome": novo_nome})


@app.route('/api/usuarios/excluir', methods=['POST'])
@exigir_login
def excluir_conta():
    with banco() as cur:
        # remove os favoritos primeiro (não há chave estrangeira ligando as tabelas,
        # então isso precisa ser feito manualmente antes de apagar o usuário)
        cur.execute("DELETE FROM favorito WHERE gmail_usuario = %s", (g.email,))
        cur.execute("DELETE FROM usuario WHERE gmail = %s", (g.email,))

    return jsonify({"mensagem": "Conta excluída com sucesso"})


if __name__ == '__main__':
    app.run()
