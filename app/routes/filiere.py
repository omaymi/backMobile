from flask import Blueprint, request, jsonify
from app import mysql  

filiere_bp = Blueprint('filiere', __name__)

@filiere_bp.route('/filieres', methods=['POST'])
def ajouter_filiere():
    data = request.get_json()
    nom = data.get('nom')

    if not nom:
        return jsonify({"error": "Le nom est requis"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO filieres (nom) VALUES (%s)", (nom,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Filière ajoutée avec succès"})

@filiere_bp.route('/filieres', methods=['GET'])
def liste_filieres():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM filieres")
    rows = cursor.fetchall()
    cursor.close()

    filieres = [{"id": row[0], "nom": row[1]} for row in rows]
    return jsonify(filieres)
