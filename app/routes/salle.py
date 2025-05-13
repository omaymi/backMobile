from flask import Blueprint, request, jsonify
from app import mysql

salle_bp = Blueprint('salle', __name__)

@salle_bp.route('/salles', methods=['POST'])
def ajouter_salle():
    data = request.get_json()
    nom = data.get('nom')
    filiere_id = data.get('filiere_id')

    if not nom or not filiere_id:
        return jsonify({"error": "Tous les champs sont requis"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO salles (nom, filiere_id) VALUES (%s, %s)", (nom, filiere_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Salle ajoutée avec succès"})


@salle_bp.route('/salles/filiere/<int:filiere_id>', methods=['GET'])
def get_salles_by_filiere(filiere_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, nom FROM salles WHERE filiere_id = %s", (filiere_id,))
    rows = cursor.fetchall()
    cursor.close()

    if rows:
        salles = [{"id": row[0], "nom": row[1]} for row in rows]
        return jsonify(salles)
    else:
        return jsonify({"error": "Aucune salle trouvée pour cette filière"}), 404


@salle_bp.route('/salles', methods=['GET'])
def liste_salles():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, nom FROM salles")
    rows = cursor.fetchall()
    cursor.close()

    salles = [{"id": row[0], "nom": row[1]} for row in rows]
    return jsonify(salles)


# disponibilite des salles
@salle_bp.route('/salles/disponibles', methods=['GET'])
def salles_disponibles():
    filiere_id = request.args.get('filiere_id')
    date = request.args.get('date')  # format: 'YYYY-MM-DD'
    heure_debut = request.args.get('heure_debut')  # format: 'HH:MM:SS'
    heure_fin = request.args.get('heure_fin')      # format: 'HH:MM:SS'

    if not all([filiere_id, date, heure_debut, heure_fin]):
        return jsonify({'error': 'Tous les paramètres sont requis (filiere_id, date, heure_debut, heure_fin)'}), 400

    cursor = mysql.connection.cursor()

    query = """
        SELECT s.id, s.nom
        FROM salles s
        WHERE s.filiere_id = %s
        AND s.nom NOT IN (
            SELECT sp.salle
            FROM seanceprofesseur sp
            WHERE sp.date = %s
            AND (%s < sp.heure_fin AND %s > sp.heure_debut)
        )
    """
    cursor.execute(query, (filiere_id, date, heure_debut, heure_fin))
    rows = cursor.fetchall()
    cursor.close()

    salles = [{"id": row[0], "nom": row[1]} for row in rows]

    return jsonify(salles)

@salle_bp.route('/salles/<int:id>', methods=['DELETE'])
def supprimer_salle(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM salles WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Salle supprimée avec succès"})