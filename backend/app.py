import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from models import db
from routes import api

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY']                     = 'shield_secret_2025'
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE']        = 'None'
app.config['SESSION_COOKIE_SECURE']          = False

CORS(app, supports_credentials=True, origins="*")

db.init_app(app)
app.register_blueprint(api, url_prefix='/api')

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Origin']      = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers']     = 'Content-Type, Authorization, Accept'
    response.headers['Access-Control-Allow-Methods']     = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin']      = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Headers']     = 'Content-Type, Authorization, Accept'
        response.headers['Access-Control-Allow-Methods']     = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200

with app.app_context():
    db.create_all()
    print('✅  Database ready.')

if __name__ == '__main__':
    print('🛡️  SHEild — Women Safety Alert System')
    print('🚀  Server  : http://localhost:5000')
    print('📡  Health  : http://localhost:5000/api/health')
    print('📱  SMS     :', '✅ ON' if os.getenv('TWILIO_SID')      else '❌ OFF — add to .env')
    print('💬  WhatsApp:', '✅ ON' if os.getenv('TWILIO_WA_PHONE') else '❌ OFF — add to .env')
    print('📧  Email   :', '✅ ON' if os.getenv('GMAIL_USER')      else '❌ OFF — add to .env')
    app.run(debug=True, port=5000, host='0.0.0.0')