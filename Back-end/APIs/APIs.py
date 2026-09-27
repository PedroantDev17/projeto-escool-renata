
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

    return psycopg2.connect(database_url, sslmode="require")


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

    conn.commit()
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
            SELECT nome, gmail, senha
            FROM usuario
            WHERE gmail = %s AND senha = %s
            LIMIT 1
            """,
            (email_user, senha_user)
        )
        resultado = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if resultado:

        nome_login = resultado[0]

        return jsonify({
            "autenticado": True,
            "usuario": nome_login
        })

    return jsonify({
        "autenticado": False
    })


if __name__ == '__main__':
    app.run()