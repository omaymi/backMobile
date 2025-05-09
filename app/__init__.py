from flask import Flask
from flask_mysqldb import MySQL

mysql = MySQL()


def create_app():
    app = Flask(__name__)
    app.secret_key = 'omaymakey'

    # Configuration MySQL
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'gestionabsia'

    mysql.init_app(app)

    # Enregistrer les routes
    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.filiere import filiere_bp
    from app.routes.module import module_bp
    from app.routes.professeur import professeur_bp
    from app.routes.seance import seance_bp

    app.register_blueprint(filiere_bp)
    app.register_blueprint(module_bp)
    app.register_blueprint(professeur_bp)
    app.register_blueprint(seance_bp)

    from app.routes.salle import salle_bp
    app.register_blueprint(salle_bp)

    return app