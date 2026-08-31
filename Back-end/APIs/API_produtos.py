from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/produtos', methods=['GET'])
def lista_produtos():
    return 'Produtos - Return'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)