"""
Point d'entrée de l'application. Charge les variables d'environnement (.env),
crée les tables si nécessaire, puis démarre le serveur de développement Flask.

Usage :
    python run.py
"""
import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db

app = create_app(os.environ.get("FLASK_ENV", "development"))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.config["DEBUG"])
