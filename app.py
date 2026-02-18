from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime as dt, timedelta
import certifi

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)  # Permite requisições do Android e de outros domínios

# Configuração do MongoDB
MONGO_URI = os.getenv("MONGO_URI")

# Usamos tlsCAFile para garantir que o Render consiga validar o certificado do Atlas
# O dnspython (no requirements) e o certifi resolvem o erro 500 de conexão
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client["geoKotlin"]            # Nome do Banco
    collection = db["locations"]        # Nome da Coleção
    # Teste de conexão opcional
    client.admin.command('ping')
    print("Conected with db!")
except Exception as e:
    print(f"db error: {e}")

@app.route('/')
def home():
    return "Server running!", 200

@app.route('/save', methods=['POST'])
def save():
    try:
        data = request.json or {}

        # Pegamos o IP para log (útil para debug)
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]

        # Criamos o registro (ajustando para o horário de Brasília -3h se desejar)
        record = {
            "ip": ip,
            "timestamp": (dt.utcnow() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Verifica se os dados do Android chegaram corretamente
        if "latitude" in data and "longitude" in data:
            record["latitude"] = data["latitude"]
            record["longitude"] = data["longitude"]
            
            # Salva no MongoDB
            collection.insert_one(record)
            
            # Removendo o _id do MongoDB para não dar erro de serialização no JSON de resposta
            if "_id" in record:
                record.pop("_id")

            return jsonify({"status": "ok", "message": "location saved", "record": record}), 201
        
        else:
            return jsonify({"status": "error", "message": "no location informed"}), 400

    except Exception as e:
        print(f"Erro ao processar save: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # O Render define a porta automaticamente pela variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
