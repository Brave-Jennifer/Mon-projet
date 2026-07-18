"""Contrôleur du dashboard statistique."""
from flask import Blueprint, render_template, current_app

from app.services import StatsService, VizService

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.route("/")
def dashboard():
    stats_service = StatsService()
    viz_service = VizService(current_app.config["GRAPH_FOLDER"])
    graphiques = viz_service.generer_tous_les_graphiques()
    indicateurs = stats_service.indicateurs_cles()
    return render_template(
        "stats/dashboard.html",
        indicateurs=indicateurs,
        graphiques=graphiques,
        occupation=stats_service.taux_occupation_lits(),
        attente=stats_service.analyse_temps_attente(),
    )
