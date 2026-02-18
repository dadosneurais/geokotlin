from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime as dt, timedelta
import certifi

load_dotenv()

app = Flask(__name__)
# O ideal é também colocar a SECRET_KEY no Render, mas deixaremos fixa ou via env
app.secret_key = os.getenv("SECRET_KEY", "chave_padrao_123") 
CORS(app)

# Puxa a senha diretamente das variáveis de ambiente do Render
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")

# Configuração do MongoDB
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client["geoKotlin"]
    collection = db["locations"]
    print("Conectado ao MongoDB!")
except Exception as e:
    print(f"Erro no banco: {e}")

# HTML de Login (Apenas senha)
LOGIN_HTML = '''
<div style="text-align:center; margin-top:100px; font-family: sans-serif;">
    <h2>Painel Restrito</h2>
    <form method="POST">
        <input type="password" name="senha" placeholder="Senha de Acesso" required style="padding:10px; border-radius:5px; border:1px solid #ccc;">
        <button type="submit" style="padding:10px 20px; cursor:pointer; background:#222; color:#fff; border:none; border-radius:5px;">Entrar</button>
    </form>
    {% if erro %}<p style="color:red;">{{ erro }}</p>{% endif %}
</div>
'''

# HTML do Dashboard
DASHBOARD_HTML = '''
<div style="font-family: sans-serif; padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2>Histórico de Localizações</h2>
        <a href="/logout" style="color:red; text-decoration:none; font-weight:bold;">Sair</a>
    </div>
    <hr>
    <table border="1" style="width:100%; text-align:left; border-collapse: collapse; margin-top:20px;">
        <tr style="background:#333; color:#fff;">
            <th style="padding:12px;">Data / Hora</th>
            <th style="padding:12px;">IP</th>
            <th style="padding:12px;">Coordenadas</th>
            <th style="padding:12px;">Mapa</th>
        </tr>
        {% for loc in dados %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding:10px;">{{ loc.timestamp }}</td>
            <td style="padding:10px;">{{ loc.ip }}</td>
            <td style="padding:10px;">{{ loc.latitude }}, {{ loc.longitude }}</td>
            <td style="padding:10px;">
                <a href="https://www.google.com/maps/search/?api=1&query={{ loc.latitude }},{{ loc.longitude }}" target="_blank" style="color:#007bff; text-decoration:none; font-weight:bold;">
                    📍 Abrir no Maps
                </a>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
'''

@app.route('/')
def home():
    if 'logado' in session:
        # Busca os 100 registros mais recentes
        dados = list(collection.find().sort("timestamp", -1).limit(100))
        return render_template_string(DASHBOARD_HTML, dados=dados)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        # Compara com a variável de ambiente do Render
        if request.form['senha'] == ACCESS_PASSWORD:
            session['logado'] = True
            return redirect(url_for('home'))
        erro = "Senha inválida!"
    return render_template_string(LOGIN_HTML, erro=erro)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

@app.route('/save', methods=['POST'])
def save():
    try:
        data = request.json or {}
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
        
        record = {
            "ip": ip,
            "timestamp": (dt.utcnow() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        }

        if "latitude" in data and "longitude" in data:
            record["latitude"] = data["latitude"]
            record["longitude"] = data["longitude"]
            collection.insert_one(record)
            return jsonify({"status": "ok"}), 201
        
        return jsonify({"status": "error", "message": "missing data"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
