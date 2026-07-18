"""Contrôleur pour la page d'accueil."""
from flask import Blueprint, render_template, current_app

from app.services import StatsService

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def accueil():
    stats = StatsService()
    indicateurs = stats.indicateurs_cles()
    return render_template("index.html", indicateurs=indicateurs)
