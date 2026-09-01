from flask import Flask, request
from flask_cors import CORS
import requests


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

    url_shopee = "https://partner.shopeemobile.com/api/v2/product/get_category?access_token=access_token&language=zh-hans&partner_id=partner_id&shop_id=shop_id&sign=sign&timestamp=timestamp"
    payload={}
    headers = {

    }
    response = requests.request("GET",url_shopee,headers=headers, data=payload, allow_redirects=False)
    print(response)
    return 'Produtos - Return'

if __name__ == '__main__':
    app.run(debug=True )