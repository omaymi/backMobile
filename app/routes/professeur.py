from flask import Blueprint, request, jsonify
from app import mysql 

professeur_bp = Blueprint('professeur', __name__)

@professeur_bp.route('/professeurs', methods=['POST'])
def ajouter_prof():
    data = request.get_json()
    nom = data.get('nom')
    email = data.get('email')
    mot_de_passe = data.get('mot_de_passe')  # tu peux le générer automatiquement si nécessaire
    filiere_id = data.get('filiere_id')
    module_id = data.get('module_id')

    if not nom or not email or not filiere_id or not module_id:
        return jsonify({"error": "Tous les champs sont requis"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO professeurs (nom, email, filiere_id, module_id, mot_de_passe)
        VALUES (%s, %s, %s, %s, %s)
    """, (nom, email, filiere_id, module_id, mot_de_passe))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Professeur ajouté avec succès"})

@professeur_bp.route('/professeurs/<int:professeur_id>/filieres', methods=['GET'])
def get_filieres_par_professeur(professeur_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT f.id, f.nom 
        FROM filieres f
        JOIN professeurs p ON f.id = p.filiere_id
        WHERE p.id = %s
    """, (professeur_id,))
    
    filieres = cursor.fetchall()
    cursor.close()

    if not filieres:
        return jsonify({"message": "Aucune filière trouvée pour ce professeur."}), 404

    filiere_list = [{"id": f[0], "nom": f[1]} for f in filieres]
    return jsonify(filiere_list)

@professeur_bp.route('/professeurs/<int:professeur_id>/filieres/<int:filiere_id>/modules', methods=['GET'])
def get_modules_par_professeur_et_filiere(professeur_id, filiere_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT m.id, m.nom
        FROM modules m
        JOIN professeurs p ON m.id = p.module_id
        WHERE p.id = %s AND p.filiere_id = %s
    """, (professeur_id, filiere_id))

    modules = cursor.fetchall()
    cursor.close()

    module_list = [{"id": m[0], "nom": m[1]} for m in modules]
    return jsonify(module_list)


@professeur_bp.route('/professeurs', methods=['GET'])
def get_professeurs_par_filiere_et_module():
    filiere_id = request.args.get('filiere_id')
    module_id = request.args.get('module_id')

    if not filiere_id or not module_id:
        return jsonify({"error": "filiere_id et module_id sont requis"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT id, nom, email FROM professeurs
        WHERE filiere_id = %s AND module_id = %s
    """, (filiere_id, module_id))

    professeurs = cursor.fetchall()
    cursor.close()

    professeur_list = [{"id": p[0], "nom": p[1], "email": p[2]} for p in professeurs]
    return jsonify(professeur_list)
@professeur_bp.route('/professeurs/filiere/<int:filiere_id>', methods=['GET'])
def get_professeurs_by_filiere(filiere_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT id, nom, filiere_id, module_id
        FROM professeurs
        WHERE filiere_id = %s
    """, (filiere_id,))
    rows = cursor.fetchall()
    cursor.close()

    if rows:
        professeurs = [{"id": row[0], "nom": row[1], "filiere_id": row[2], "module_id": row[3]} for row in rows]
        return jsonify(professeurs)
    else:
        return jsonify({"error": "Aucun professeur trouvé pour cette filière"}), 404
@professeur_bp.route('/professeurs/<int:id>', methods=['DELETE'])
def supprimer_professeur(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM professeurs WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Professeur supprimé avec succès"})