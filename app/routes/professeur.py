from flask import Blueprint, request, jsonify
from app import mysql 

professeur_bp = Blueprint('professeur', __name__)

@professeur_bp.route('/professeurs', methods=['POST'])
def ajouter_prof():
    data = request.get_json()
    nom = data.get('nom')
    email = data.get('email')
    filiere_id = data.get('filiere_id')
    module_id = data.get('module_id')

    if not nom or not email or not filiere_id or not module_id:
        return jsonify({"error": "Tous les champs sont requis"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO professeurs (nom, email, filiere_id, module_id)
        VALUES (%s, %s, %s, %s)
    """, (nom, email, filiere_id, module_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Professeur ajouté avec succès"})
