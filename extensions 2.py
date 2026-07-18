"""
Instanciation des extensions Flask, séparées pour éviter les imports circulaires.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
