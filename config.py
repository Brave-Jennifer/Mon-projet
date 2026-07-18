"""
Configuration de l'application, chargée depuis les variables d'environnement (.env).
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    """Configuration de base commune à tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-moi-en-production")

    # PostgreSQL en production (recommandé) :
    #   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/chu_pediatrie
    # Un fallback SQLite est fourni pour permettre de lancer/tester le projet
    # immédiatement sans serveur PostgreSQL installé.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'chu_pediatrie.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads", "patients")
    GRAPH_FOLDER = os.path.join(BASE_DIR, "app", "static", "graphs")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 Mo max pour les uploads

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # Contraintes métier (valeurs par défaut, modifiables ici)
    MAX_CONSULTATIONS_PAR_JOUR_MEDECIN = 20
    DUREE_MAX_TRAITEMENT_JOURS = 90
    DUREES_CONSULTATION_AUTORISEES = (15, 30, 60)

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
