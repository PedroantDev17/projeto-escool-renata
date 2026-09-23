# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import requests
# import serpapi
# import sqlite3

# banco = sqlite3.connect('Back-end/banco.db', check_same_thread=False)
# cursor = banco.cursor()

# app = Flask(__name__)
# # Mecanismo de Segurança 
# CORS(app)

# @app.route('/produtos', methods=['POST'])
# def lista_produtos():
#     # Pegando informações da API Produto.js:
#     url = 'https://commute-doormat-operator.ngrok-free.dev/produtos' 
#     # Resposta da API ( 200, 401..)
#     resposta = requests.get(url)
#     print(resposta.status_code)

#     # Retirando Informações dentro da API:
#     info = request.get_json()
#     print(info)
#     produto = info['nomeProduto']

#     # Consultando produtos
#     client = serpapi.Client(api_key="a8c241eafd2cd20e0de947b1f9bdeef39585c2615f2e707a173cc7319ae2d5b2")
#     results = client.search({
#     "engine": "google_shopping",
#     "q": produto,
#     "location": "Brazil",
#     "hl": "pt-br",
#     "gl": "br"
#     })
#     # Resultado da pesquisa
#     produtos_encontrados = results["shopping_results"]

#     lista = []

#     # Laço for para Retirar de JSON:
#     for item in produtos_encontrados:
#         produtos_list = { "imagem" : item.get("thumbnail"),
#         "posicao" : item.get("position"),
#         "Icon_loja" : item.get("source_icon"),
#         "title" : item.get("title"),
#         "nota" : item.get("rating"),
#         "compras" : item.get("reviews"),
#         'preco' : item.get("price"),
#         "loja" : item.get("source"),
#         "link" : item.get("product_link")
#         }
#         # Colocando em uma lista
#         lista.append(produtos_list)

#     # Retornando a Resposta para API protudo.js
#     return jsonify(lista)
# # API - Categorias
# @app.route('/categoria', methods=['POST'])
# def categoria():
#      # Consultando produtos
#         client = serpapi.Client(api_key="a8c241eafd2cd20e0de947b1f9bdeef39585c2615f2e707a173cc7319ae2d5b2")
#         results = client.search({
#         "engine": "google_shopping",
#         "q": "eletronicos",
#         "location": "Brazil",
#         "hl": "pt-br",
#         "gl": "br"
#         })
#         # Resultado da pesquisa
#         produtos_encontrados = results["shopping_results"]
    
#         lista = []
    
#         # Laço for para Retirar de JSON:
#         for item in produtos_encontrados:
#             produtos_list = { "imagem" : item.get("thumbnail"),
#             "posicao" : item.get("position"),
#             "Icon_loja" : item.get("source_icon"),
#             "title" : item.get("title"),
#             "nota" : item.get("rating"),
#             "compras" : item.get("reviews"),
#             'preco' : item.get("price"),
#             "loja" : item.get("source"),
#             "link" : item.get("product_link")
#             }
#             # Colocando em uma lista
#             lista.append(produtos_list)
    
#         # Retornando a Resposta para API protudo.js
#         return jsonify(lista)
# # API - Usuarios
# @app.route('/usuarios', methods=['POST'])
# def users():
#     banco.execute("""CREATE TABLE IF NOT EXISTS usuario (
#        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
#     nome varchar(50),
#       gmail varchar(250),
#       senha varchar(50)
# );""")
#     # Pegando dados do Usuario na API:
#     url_users = 'https://commute-doormat-operator.ngrok-free.dev/usuarios'
#     # Resposta da API:
#     resposta = requests.get(url_users)
#     print(resposta)

#     # Retirando informações:
#     info_users = request.get_json()
#     print(info_users)

#     nome = info_users["nome"]
#     gmail = info_users["email"]
#     senha = info_users["senha"]


#     cursor.execute("INSERT INTO usuario (nome, gmail, senha) VALUES (?, ?, ?)", (nome, gmail, senha) )
#     banco.commit()    

#     return jsonify({"mensagem":"200"})

# @app.route('/login', methods=['POST'])
# def login():

#     login_user = 'https://commute-doormat-operator.ngrok-free.dev/login'

#     resposta = requests.get(login_user)
#     print(resposta)

#     #Retirando da API:
#     login_json = request.get_json()
#     print(login_json)

#     senha_user = login_json["senha"]
#     email_user = login_json["email"]

#     # Selecionando gmail e senha no Banco de Dados
#     cursor.execute("SELECT nome, gmail, senha FROM usuario WHERE gmail = ? AND senha = ? LIMIT 1", (email_user, senha_user))
    
#     # Pega apenas uma linha de resultado da consulta
#     resultado = cursor.fetchone()
#     print(resultado)
#     # confirmando autenticação
#     if resultado:
#         nome_login = resultado[0]
#         return jsonify({"autenticado": True, "usuario": nome_login })
#     else:
#         return jsonify({"autenticado": False})
# if __name__ == '__main__':
#     app.run(debug=True )

from flask import Flask, request, jsonify
from flask_cors import CORS
import serpapi
import sqlite3

# Configuração do Banco de Dados local (temporário para a nuvem)
banco = sqlite3.connect('Back-end/banco.db', check_same_thread=False)
cursor = banco.cursor()

app = Flask(__name__)
CORS(app)

@app.route('/api/produtos', methods=['POST'])
def lista_produtos():
    # Retirando Informações dentro da requisição do frontend:
    info = request.get_json()
    produto = info.get('nomeProduto', '')

    # Consultando produtos no SerpAPI
    client = serpapi.Client(api_key="a8c241eafd2cd20e0de947b1f9bdeef39585c2615f2e707a173cc7319ae2d5b2")
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
            "imagem" : item.get("thumbnail"),
            "posicao" : item.get("position"),
            "Icon_loja" : item.get("source_icon"),
            "title" : item.get("title"),
            "nota" : item.get("rating"),
            "compras" : item.get("reviews"),
            'preco' : item.get("price"),
            "loja" : item.get("source"),
            "link" : item.get("product_link")
        }
        lista.append(produtos_list)

    return jsonify(lista)

@app.route('/api/categoria', methods=['POST'])
def categoria():
    # Consultando categorias padrão no SerpAPI
    client = serpapi.Client(api_key="a8c241eafd2cd20e0de947b1f9bdeef39585c2615f2e707a173cc7319ae2d5b2")
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
            "imagem" : item.get("thumbnail"),
            "posicao" : item.get("position"),
            "Icon_loja" : item.get("source_icon"),
            "title" : item.get("title"),
            "nota" : item.get("rating"),
            "compras" : item.get("reviews"),
            'preco' : item.get("price"),
            "loja" : item.get("source"),
            "link" : item.get("product_link")
        }
        lista.append(produtos_list)

    return jsonify(lista)

@app.route('/api/usuarios', methods=['POST'])
def users():
    banco.execute("""CREATE TABLE IF NOT EXISTS usuario (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nome varchar(50),
        gmail varchar(250),
        senha varchar(50)
    );""")

    # Retirando informações diretas vindas do Frontend:
    info_users = request.get_json()
    nome = info_users.get("nome")
    gmail = info_users.get("email")
    senha = info_users.get("senha")

    cursor.execute("INSERT INTO usuario (nome, gmail, senha) VALUES (?, ?, ?)", (nome, gmail, senha))
    banco.commit()    

    return jsonify({"mensagem":"200"})

@app.route('/api/login', methods=['POST'])
def login():
    # Retirando dados diretos enviados pelo formulário do Frontend:
    login_json = request.get_json()
    senha_user = login_json.get("senha")
    email_user = login_json.get("email")

    # Selecionando no Banco de Dados
    cursor.execute("SELECT nome, gmail, senha FROM usuario WHERE gmail = ? AND senha = ? LIMIT 1", (email_user, senha_user))
    resultado = cursor.fetchone()
    
    if resultado:
        nome_login = resultado[0]
        return jsonify({"autenticado": True, "usuario": nome_login})
    else:
        return jsonify({"autenticado": False})

# Importante para a Vercel reconhecer a inicialização da Serverless Function
if __name__ == '__main__':
    app.run(debug=True)
