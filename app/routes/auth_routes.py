from flask import Blueprint, request, jsonify, session
from app import mysql
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return jsonify({"message": "Bienvenue sur l'API Flask!"})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email et mot de passe sont requis"}), 400

    email = data['email']
    password = data['password']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
        session['user_id'] = user[0]
        return jsonify({"message": "Connexion réussie", "user_id": user[0]})
    else:
        return jsonify({"error": "Email ou mot de passe incorrect"}), 401
