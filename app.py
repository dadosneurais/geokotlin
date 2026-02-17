from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime as dt

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)  # Permite requisições externas

# Conecta ao MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["geoKotlin"]            # Banco de dados
collection = db["locations"]        # Coleção

@app.route('/')
def home():
    return "Servidor rodando!", 200

@app.route('/save', methods=['POST'])
def save():
    data = request.json or {}

    record = {
        "timestamp": dt.utcnow(),
    }

    if "latitude" in data and "longitude" in data:
        record["latitude"] = data["latitude"]
        record["longitude"] = data["longitude"]

    # Salva no MongoDB
    collection.insert_one(record)

    return jsonify({"status": "ok", "record": record}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
