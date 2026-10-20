from flask import Flask, request, jsonify, g
from flask_cors import CORS
import serpapi
import psycopg2
import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Limite de tentativas de login por senha
MAX_TENTATIVAS = 5
BLOQUEIO_MINUTOS = 15

# Token de login (JWT). JWT_SECRET deve ser uma string longa e aleatória,
# configurada nas variáveis de ambiente da Vercel.
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_DIAS = 7


def gerar_token(email):
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET não configurada")

    payload = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_DIAS)
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
            dados = jwt.decode(cabecalho[7:], JWT_SECRET, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Sessão inválida ou expirada. Faça login novamente."}), 401

        g.email = dados["email"]
        return f(*args, **kwargs)
    return wrapper


def get_conn():
    """
    Abre uma conexão nova com o Postgres a cada chamada.
    Em ambiente serverless (Vercel) não dá pra manter uma conexão
    global viva entre execuções — por isso abrimos e fechamos
    a conexão dentro de cada request.
    """
    from urllib.parse import urlsplit, unquote

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
        )

    raise RuntimeError(
        "Nenhuma variável de conexão com o banco encontrada "
        "(DATABASE_POSTGRES_URL / DATABASE_URL / POSTGRES_URL ou "
        "DATABASE_POSTGRES_HOST/USER/PASSWORD/DATABASE)"
    )


def criar_tabela_se_nao_existir():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id_usuario SERIAL PRIMARY KEY,
        nome VARCHAR(50),
        gmail VARCHAR(250),
        senha VARCHAR(50)
    )
    """)

    # garante a coluna 'foto' mesmo se a tabela já existir de antes
    cursor.execute("""
    ALTER TABLE usuario ADD COLUMN IF NOT EXISTS foto VARCHAR(500)
    """)

    # o hash da senha é bem maior que 50 caracteres, então ampliamos a coluna
    cursor.execute("""
    ALTER TABLE usuario ALTER COLUMN senha TYPE VARCHAR(255)
    """)

    # controle de tentativas de login (limite de tentativas de senha)
    cursor.execute("""
    ALTER TABLE usuario ADD COLUMN IF NOT EXISTS tentativas_falhas INTEGER NOT NULL DEFAULT 0
    """)

    cursor.execute("""
    ALTER TABLE usuario ADD COLUMN IF NOT EXISTS bloqueado_ate TIMESTAMPTZ
    """)

    # impede duas contas com o mesmo e-mail, seja criada por senha ou por Google
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_usuario_gmail_unico ON usuario (gmail)
    """)

    cursor.execute("""
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

    conn.commit()
    cursor.close()
    conn.close()


def buscar_ou_criar_usuario(email, nome, foto, criar=False):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT nome, gmail FROM usuario WHERE gmail = %s LIMIT 1",
            (email,)
        )
        resultado = cursor.fetchone()

        if resultado:
            # já existe: atualiza a foto (pode ter mudado no Google) e retorna
            cursor.execute(
                "UPDATE usuario SET foto = %s WHERE gmail = %s",
                (foto, email)
            )
            conn.commit()
            return {"nome": resultado[0], "email": resultado[1], "foto": foto}

        # não existe: só cria se a chamada veio da página de criar conta
        if not criar:
            return None

        # cria um novo usuário (sem senha, já que é login via Google)
        cursor.execute(
            "INSERT INTO usuario (nome, gmail, foto) VALUES (%s, %s, %s)",
            (nome, email, foto)
        )
        conn.commit()
        return {"nome": nome, "email": email, "foto": foto}
    finally:
        cursor.close()
        conn.close()


# Garante que a tabela existe quando a API sobe
try:
    criar_tabela_se_nao_existir()
except Exception as e:
    print("Falha ao criar tabela:", e)


@app.route('/api/produtos', methods=['POST'])
def lista_produtos():

    info = request.get_json()

    if not info:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    produto = info.get('nomeProduto', '')

    if not produto:
        return jsonify({"erro": "nomeProduto não informado"}), 400

    api_key = os.environ.get("SERPAPI_KEY")

    if not api_key:
        return jsonify({"erro": "SERPAPI_KEY não configurada"}), 500

    client = serpapi.Client(api_key=api_key)

    results = client.search({
        "engine": "google_shopping",
        "q": produto,
        "location": "Brazil",
        "hl": "pt-br",
        "gl": "br"
    })

    produtos_encontrados = results.get("shopping_results", [])

    lista = []

    for item in produtos_encontrados:

        produtos_list = {
            "imagem": item.get("thumbnail"),
            "posicao": item.get("position"),
            "Icon_loja": item.get("source_icon"),
            "title": item.get("title"),
            "nota": item.get("rating"),
            "compras": item.get("reviews"),
            "preco": item.get("price"),
            "loja": item.get("source"),
            "link": item.get("product_link")
        }

        lista.append(produtos_list)

    return jsonify(lista)


@app.route('/api/categoria', methods=['POST'])
def categoria():

    api_key = os.environ.get("SERPAPI_KEY")

    if not api_key:
        return jsonify({"erro": "SERPAPI_KEY não configurada"}), 500

    client = serpapi.Client(api_key=api_key)

    results = client.search({
        "engine": "google_shopping",
        "q": "eletronicos",
        "location": "Brazil",
        "hl": "pt-br",
        "gl": "br"
    })

    produtos_encontrados = results.get("shopping_results", [])

    lista = []

    for item in produtos_encontrados:

        produtos_list = {
            "imagem": item.get("thumbnail"),
            "posicao": item.get("position"),
            "Icon_loja": item.get("source_icon"),
            "title": item.get("title"),
            "nota": item.get("rating"),
            "compras": item.get("reviews"),
            "preco": item.get("price"),
            "loja": item.get("source"),
            "link": item.get("product_link")
        }

        lista.append(produtos_list)

    return jsonify(lista)


@app.route('/api/usuarios', methods=['POST'])
def users():

    info_users = request.get_json()

    if not info_users:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    nome = info_users.get("nome")
    gmail = info_users.get("email")
    senha = info_users.get("senha")

    if not nome or not gmail or not senha:
        return jsonify({
            "erro": "nome, email e senha são obrigatórios"
        }), 400

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id_usuario FROM usuario WHERE gmail = %s LIMIT 1",
            (gmail,)
        )
        ja_existe = cursor.fetchone()

        if ja_existe:
            return jsonify({
                "erro": "Já existe uma conta com esse e-mail."
            }), 409

        cursor.execute(
            """
            INSERT INTO usuario (nome, gmail, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, gmail, generate_password_hash(senha))
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "mensagem": "Usuário cadastrado com sucesso"
    }), 201


@app.route('/api/login-google', methods=['POST'])
def login_google():
    dados = request.get_json(silent=True) or {}
    token = dados.get('token')
    # só cria conta nova se o front-end pedir explicitamente (página de criar conta)
    criar = dados.get('criar') is True
    try:
        info = id_token.verify_oauth2_token(
            token, grequests.Request(), os.environ.get('GOOGLE_CLIENT_ID')
        )
    except ValueError:
        return jsonify({"erro": "token inválido"}), 401

    email = info['email']
    nome = info['name']
    foto = info['picture']

    usuario = buscar_ou_criar_usuario(email, nome, foto, criar)

    if usuario is None:
        return jsonify({
            "erro": "Não existe uma conta com esse e-mail. Crie uma conta primeiro."
        }), 404

    usuario["token"] = gerar_token(email)
    return jsonify(usuario)


@app.route('/api/login', methods=['POST'])
def login():

    login_json = request.get_json()

    if not login_json:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    senha_user = login_json.get("senha")
    email_user = login_json.get("email")

    if not email_user or not senha_user:
        return jsonify({
            "erro": "email e senha são obrigatórios"
        }), 400

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # O cálculo do bloqueio é feito no próprio banco (NOW()),
        # assim não há problema de fuso horário entre Python e Postgres
        cursor.execute(
            """
            SELECT nome, gmail, senha, foto,
                   CASE WHEN bloqueado_ate > NOW()
                        THEN CEIL(EXTRACT(EPOCH FROM (bloqueado_ate - NOW())))
                        ELSE 0 END
            FROM usuario
            WHERE gmail = %s
            LIMIT 1
            """,
            (email_user,)
        )
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({"autenticado": False})

        nome_login, gmail_login, senha_db, foto_login, segundos_bloqueio = resultado

        if senha_db is None:
            # conta existe, mas foi criada via Google — nunca teve senha
            return jsonify({
                "autenticado": False,
                "erro": "Gmail ou senha não encontrado, tente novamente."
            }), 400

        # 1) Conta bloqueada? Recusa mesmo que a senha esteja certa
        if segundos_bloqueio > 0:
            return resposta_bloqueio(segundos_bloqueio)

        # 2) Confere a senha. Aceita o hash novo e também contas antigas
        # com senha em texto puro (que são convertidas para hash no login).
        senha_ok = False
        precisa_migrar = False

        if senha_db.startswith(("scrypt:", "pbkdf2:")):
            senha_ok = check_password_hash(senha_db, senha_user)
        elif senha_db == senha_user:
            senha_ok = True
            precisa_migrar = True

        # Senha correta: zera o contador (e converte para hash, se ainda era texto puro)
        if senha_ok:
            novo_valor = generate_password_hash(senha_user) if precisa_migrar else senha_db
            cursor.execute(
                """
                UPDATE usuario
                SET senha = %s, tentativas_falhas = 0, bloqueado_ate = NULL
                WHERE gmail = %s
                """,
                (novo_valor, email_user)
            )
            conn.commit()

            return jsonify({
                "autenticado": True,
                "usuario": nome_login,
                "nome": nome_login,
                "email": gmail_login,
                "foto": foto_login,
                "token": gerar_token(gmail_login)
            })

        # 3) Senha errada: incrementa; ao atingir o limite, bloqueia e zera o contador
        cursor.execute(
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
            (MAX_TENTATIVAS, BLOQUEIO_MINUTOS, MAX_TENTATIVAS, email_user)
        )
        segundos_restantes = cursor.fetchone()[0]
        conn.commit()

        # Se esta tentativa atingiu o limite, já avisa o bloqueio (e a contagem)
        if segundos_restantes > 0:
            return resposta_bloqueio(segundos_restantes)

        return jsonify({"autenticado": False})
    finally:
        cursor.close()
        conn.close()


@app.route('/api/favoritos/adicionar', methods=['POST'])
@exigir_login
def adicionar_favorito():

    info = request.get_json(silent=True) or {}

    # o e-mail vem do token, não do corpo da requisição
    gmail = g.email
    titulo = info.get('titulo')
    imagem = info.get('imagem')
    preco = info.get('preco')
    loja = info.get('loja')
    link = info.get('link')

    if not titulo:
        return jsonify({"erro": "titulo é obrigatório"}), 400

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO favorito (gmail_usuario, titulo, imagem, preco, loja, link)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (gmail, titulo, imagem, preco, loja, link)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"mensagem": "Favorito adicionado com sucesso"}), 201


@app.route('/api/favoritos/listar', methods=['POST'])
@exigir_login
def listar_favoritos():

    gmail = g.email

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id_favorito, titulo, imagem, preco, loja, link
            FROM favorito
            WHERE gmail_usuario = %s
            ORDER BY id_favorito DESC
            """,
            (gmail,)
        )
        resultados = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    lista = []
    for linha in resultados:
        lista.append({
            "id_favorito": linha[0],
            "titulo": linha[1],
            "imagem": linha[2],
            "preco": linha[3],
            "loja": linha[4],
            "link": linha[5]
        })

    return jsonify(lista)


@app.route('/api/favoritos/remover', methods=['POST'])
@exigir_login
def remover_favorito():

    info = request.get_json(silent=True) or {}

    id_favorito = info.get('id_favorito')
    gmail = g.email

    if not id_favorito:
        return jsonify({"erro": "id_favorito é obrigatório"}), 400

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM favorito WHERE id_favorito = %s AND gmail_usuario = %s",
            (id_favorito, gmail)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"mensagem": "Favorito removido com sucesso"})


@app.route('/api/usuarios/atualizar-nome', methods=['POST'])
@exigir_login
def atualizar_nome():

    info = request.get_json(silent=True) or {}

    gmail = g.email
    novo_nome = info.get('nome')

    if not novo_nome:
        return jsonify({"erro": "nome é obrigatório"}), 400

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE usuario SET nome = %s WHERE gmail = %s",
            (novo_nome, gmail)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"mensagem": "Nome atualizado com sucesso", "nome": novo_nome})


@app.route('/api/usuarios/excluir', methods=['POST'])
@exigir_login
def excluir_conta():

    gmail = g.email

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # remove os favoritos primeiro (não há chave estrangeira ligando as tabelas,
        # então isso precisa ser feito manualmente antes de apagar o usuário)
        cursor.execute("DELETE FROM favorito WHERE gmail_usuario = %s", (gmail,))
        cursor.execute("DELETE FROM usuario WHERE gmail = %s", (gmail,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"mensagem": "Conta excluída com sucesso"})


if __name__ == '__main__':
    app.run()