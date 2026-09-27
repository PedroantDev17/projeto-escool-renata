
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import serpapi
# import sqlite3
# import os

# app = Flask(__name__)
# CORS(app)

# # Banco temporário da Vercel
# banco_path = "/tmp/banco.db"

# banco = sqlite3.connect(
#     banco_path,
#     check_same_thread=False
# )

# cursor = banco.cursor()

# # Cria a tabela quando a API iniciar
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS usuario (
#     id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
#     nome VARCHAR(50),
#     gmail VARCHAR(250),
#     senha VARCHAR(50)
# )
# """)

# banco.commit()


# @app.route('/api/produtos', methods=['POST'])
# def lista_produtos():

#     info = request.get_json()

#     if not info:
#         return jsonify({"erro": "Nenhum JSON recebido"}), 400

#     produto = info.get('nomeProduto', '')

#     if not produto:
#         return jsonify({"erro": "nomeProduto não informado"}), 400

#     api_key = os.environ.get("SERPAPI_KEY")

#     if not api_key:
#         return jsonify({"erro": "SERPAPI_KEY não configurada"}), 500

#     client = serpapi.Client(api_key=api_key)

#     results = client.search({
#         "engine": "google_shopping",
#         "q": produto,
#         "location": "Brazil",
#         "hl": "pt-br",
#         "gl": "br"
#     })

#     produtos_encontrados = results.get("shopping_results", [])

#     lista = []

#     for item in produtos_encontrados:

#         produtos_list = {
#             "imagem": item.get("thumbnail"),
#             "posicao": item.get("position"),
#             "Icon_loja": item.get("source_icon"),
#             "title": item.get("title"),
#             "nota": item.get("rating"),
#             "compras": item.get("reviews"),
#             "preco": item.get("price"),
#             "loja": item.get("source"),
#             "link": item.get("product_link")
#         }

#         lista.append(produtos_list)

#     return jsonify(lista)


# @app.route('/api/categoria', methods=['POST'])
# def categoria():

#     api_key = os.environ.get("SERPAPI_KEY")

#     if not api_key:
#         return jsonify({"erro": "SERPAPI_KEY não configurada"}), 500

#     client = serpapi.Client(api_key=api_key)

#     results = client.search({
#         "engine": "google_shopping",
#         "q": "eletronicos",
#         "location": "Brazil",
#         "hl": "pt-br",
#         "gl": "br"
#     })

#     produtos_encontrados = results.get("shopping_results", [])

#     lista = []

#     for item in produtos_encontrados:

#         produtos_list = {
#             "imagem": item.get("thumbnail"),
#             "posicao": item.get("position"),
#             "Icon_loja": item.get("source_icon"),
#             "title": item.get("title"),
#             "nota": item.get("rating"),
#             "compras": item.get("reviews"),
#             "preco": item.get("price"),
#             "loja": item.get("source"),
#             "link": item.get("product_link")
#         }

#         lista.append(produtos_list)

#     return jsonify(lista)


# @app.route('/api/usuarios', methods=['POST'])
# def users():

#     info_users = request.get_json()

#     if not info_users:
#         return jsonify({"erro": "Nenhum JSON recebido"}), 400

#     nome = info_users.get("nome")
#     gmail = info_users.get("email")
#     senha = info_users.get("senha")

#     if not nome or not gmail or not senha:
#         return jsonify({
#             "erro": "nome, email e senha são obrigatórios"
#         }), 400

#     cursor.execute(
#         """
#         INSERT INTO usuario (nome, gmail, senha)
#         VALUES (?, ?, ?)
#         """,
#         (nome, gmail, senha)
#     )

#     banco.commit()

#     return jsonify({
#         "mensagem": "Usuário cadastrado com sucesso"
#     }), 201


# @app.route('/api/login', methods=['POST'])
# def login():

#     login_json = request.get_json()

#     if not login_json:
#         return jsonify({"erro": "Nenhum JSON recebido"}), 400

#     senha_user = login_json.get("senha")
#     email_user = login_json.get("email")

#     if not email_user or not senha_user:
#         return jsonify({
#             "erro": "email e senha são obrigatórios"
#         }), 400

#     cursor.execute(
#         """
#         SELECT nome, gmail, senha
#         FROM usuario
#         WHERE gmail = ? AND senha = ?
#         LIMIT 1
#         """,
#         (email_user, senha_user)
#     )

#     resultado = cursor.fetchone()

#     if resultado:

#         nome_login = resultado[0]

#         return jsonify({
#             "autenticado": True,
#             "usuario": nome_login
#         })

#     return jsonify({
#         "autenticado": False
#     })


# if __name__ == '__main__':
#     app.run()
from flask import Flask, request, jsonify
from flask_cors import CORS
import serpapi
import psycopg2
import os
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

app = Flask(__name__)
CORS(app)


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


def buscar_ou_criar_usuario(email, nome, foto):
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

        # não existe: cria um novo usuário (sem senha, já que é login via Google)
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
criar_tabela_se_nao_existir()


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
                "erro": "Já existe uma conta com esse e-mail. Tente fazer login."
            }), 409

        cursor.execute(
            """
            INSERT INTO usuario (nome, gmail, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, gmail, senha)
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
    token = request.json.get('token')
    try:
        info = id_token.verify_oauth2_token(
            token, grequests.Request(), os.environ.get('GOOGLE_CLIENT_ID')
        )
    except ValueError:
        return jsonify({"erro": "token inválido"}), 401

    email = info['email']
    nome = info['name']
    foto = info['picture']

    usuario = buscar_ou_criar_usuario(email, nome, foto)
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
        cursor.execute(
            """
            SELECT nome, gmail, senha, foto
            FROM usuario
            WHERE gmail = %s
            LIMIT 1
            """,
            (email_user,)
        )
        resultado = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if resultado and resultado[2] is None:
        # conta existe, mas foi criada via Google — nunca teve senha
        return jsonify({
            "autenticado": False,
            "erro": "Essa conta usa login com Google. Use o botão 'Fazer Login com o Google'."
        }), 400

    if resultado and resultado[2] == senha_user:

        nome_login = resultado[0]
        foto_login = resultado[3]

        return jsonify({
            "autenticado": True,
            "usuario": nome_login,
            "nome": nome_login,
            "email": resultado[1],
            "foto": foto_login
        })

    return jsonify({
        "autenticado": False
    })


@app.route('/api/favoritos/adicionar', methods=['POST'])
def adicionar_favorito():

    info = request.get_json()

    if not info:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    gmail = info.get('gmail')
    titulo = info.get('titulo')
    imagem = info.get('imagem')
    preco = info.get('preco')
    loja = info.get('loja')
    link = info.get('link')

    if not gmail or not titulo:
        return jsonify({"erro": "gmail e titulo são obrigatórios"}), 400

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
def listar_favoritos():

    info = request.get_json()

    if not info:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    gmail = info.get('gmail')

    if not gmail:
        return jsonify({"erro": "gmail é obrigatório"}), 400

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
def remover_favorito():

    info = request.get_json()

    if not info:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    id_favorito = info.get('id_favorito')
    gmail = info.get('gmail')

    if not id_favorito or not gmail:
        return jsonify({"erro": "id_favorito e gmail são obrigatórios"}), 400

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
def atualizar_nome():

    info = request.get_json()

    if not info:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    gmail = info.get('gmail')
    novo_nome = info.get('nome')

    if not gmail or not novo_nome:
        return jsonify({"erro": "gmail e nome são obrigatórios"}), 400

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
def excluir_conta():

    info = request.get_json()

    if not info:
        return jsonify({"erro": "Nenhum JSON recebido"}), 400

    gmail = info.get('gmail')

    if not gmail:
        return jsonify({"erro": "gmail é obrigatório"}), 400

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