from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import serpapi

app = Flask(__name__)
# Mecanismo de Segurança 
CORS(app)

@app.route('/produtos', methods=['POST'])
def lista_produtos():
    # Pegando informações da API Produto.js:
    url = 'https://commute-doormat-operator.ngrok-free.dev/produtos' 
    # Resposta da API ( 200, 401..)
    resposta = requests.get(url)
    print(resposta.status_code)

    # Retirando Informações dentro da API:
    info = request.get_json()
    print(info)
    produto = info['nomeProduto']

    # Consultando produtos
    client = serpapi.Client(api_key="a8c241eafd2cd20e0de947b1f9bdeef39585c2615f2e707a173cc7319ae2d5b2")
    results = client.search({
        "engine": "google_shopping",
        "q": produto,
        "gl": "br",
        "hl": "pt-br"
    })

    # Resultado da pesquisa
    produtos_encontrados = results["shopping_results"]

    lista = []

    # Laço for para Retirar de JSON:
    for item in produtos_encontrados:
        produtos_list = { "imagem" : item.get("thumbnail"),
        "posicao" : item.get("position"),
        "Icon_loja" : item.get("source_icon"),
        "title" : item.get("title"),
        'preco' : item.get("price"),
        "loja" : item.get("source"),
        "link" : item.get("product_link")
        }
        # Colocando em uma lista
        lista.append(produtos_list)

    # Retornando a Resposta para API protudo.js
    return jsonify(lista)

if __name__ == '__main__':
    app.run(debug=True )