from flask import Blueprint, request, jsonify
from app import mysql

module_bp = Blueprint('module', __name__)


@module_bp.route('/modules', methods=['POST'])
def ajouter_module():
    data = request.get_json()
    nom = data.get('nom')
    filiere_id = data.get('filiere_id')

    if not nom or not filiere_id:
        return jsonify({"error": "Tous les champs sont requis"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO modules (nom, filiere_id) VALUES (%s, %s)", (nom, filiere_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Module ajouté avec succès"})


@module_bp.route('/modules/filiere/<int:filiere_id>', methods=['GET'])
def get_modules_by_filiere(filiere_id):
    cursor = mysql.connection.cursor()

    # Exécuter une requête SQL pour récupérer tous les modules associés à cette filière
    cursor.execute("""
        SELECT m.id, m.nom
        FROM modules m
        WHERE m.filiere_id = %s
    """, (filiere_id,))

    rows = cursor.fetchall()
    cursor.close()

    if rows:
        # Si des modules sont trouvés, les retourner sous forme de JSON
        modules = [{"id": row[0], "nom": row[1]} for row in rows]
        return jsonify(modules)
    else:
        # Si aucun module n'est trouvé pour cette filière
        return jsonify({"error": "Aucun module trouvé pour cette filière"}), 404


@module_bp.route('/modules', methods=['GET'])
def liste_modules():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM modules")
    rows = cursor.fetchall()
    cursor.close()

    modules = [{"id": row[0], "nom": row[1]} for row in rows]

    return jsonify(modules)