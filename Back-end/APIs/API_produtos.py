from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import serpapi

app = Flask(__name__)
CORS(app)

@app.route('/produtos', methods=['POST'])
def lista_produtos():
    # Pegando informações na API
    url = 'https://commute-doormat-operator.ngrok-free.dev/produtos' 
    
    resposta = requests.get(url)
    print(resposta.status_code)

    info = request.get_json()
    print(info)
    produto = info['nomeProduto']


    client = serpapi.Client(api_key="a8c241eafd2cd20e0de947b1f9bdeef39585c2615f2e707a173cc7319ae2d5b2")
    results = client.search({
        "engine": "google_shopping",
        "q": produto,
        "gl": "br",
        "hl": "pt-br"
    })


    produtos_encontrados = results["shopping_results"]

    for item in produtos_encontrados:
        posicao = item.get("position")
        Icon_loja = item.get("source_icon")
        title = item.get("title")
        preco = item.get("price")
        loja = item.get("source")
        link = item.get("product_link")

    return jsonify({"resposta": "200",
                    "posicao": posicao,
                    "icon_loja": Icon_loja,
                    "titulo": title,
                    "preco": preco,
                    "loja_name": loja,
                    "link_product": link})

if __name__ == '__main__':
    app.run(debug=True )