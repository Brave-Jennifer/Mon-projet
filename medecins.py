"""Contrôleur Médecins : liste et planning."""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Medecin, ValidationError

medecins_bp = Blueprint("medecins", __name__, url_prefix="/medecins")


@medecins_bp.route("/")
def liste():
    medecins = Medecin.query.order_by(Medecin.nom).all()
    return render_template("medecins/list.html", medecins=medecins)


@medecins_bp.route("/nouveau", methods=["GET", "POST"])
def creer():
    if request.method == "POST":
        try:
            medecin = Medecin(
                nom=request.form["nom"].strip(),
                prenom=request.form["prenom"].strip(),
                specialite=request.form["specialite"].strip(),
                numero_ordre=request.form["numero_ordre"].strip(),
            )
            medecin.valider()
            db.session.add(medecin)
            db.session.commit()
            flash(f"{medecin.nom_complet} ajouté.", "success")
            return redirect(url_for("medecins.liste"))
        except ValidationError as e:
            flash(str(e), "danger")
    return render_template("medecins/form.html")


@medecins_bp.route("/<int:medecin_id>")
def detail(medecin_id):
    medecin = Medecin.query.get_or_404(medecin_id)
    return render_template("medecins/detail.html", medecin=medecin)
