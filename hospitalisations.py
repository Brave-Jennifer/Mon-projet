"""Contrôleur Hospitalisations : admission, suivi quotidien, sortie."""
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Hospitalisation, SuiviQuotidien, Patient, Medecin, Consultation, ValidationError

hospitalisations_bp = Blueprint("hospitalisations", __name__, url_prefix="/hospitalisations")


@hospitalisations_bp.route("/")
def liste():
    hospitalisations = Hospitalisation.query.order_by(
        Hospitalisation.date_entree.desc()).all()
    return render_template("hospitalisations/list.html", hospitalisations=hospitalisations)


@hospitalisations_bp.route("/nouvelle", methods=["GET", "POST"])
def creer():
    patients = Patient.query.all()
    medecins = Medecin.query.all()
    if request.method == "POST":
        try:
            patient_id = int(request.form["patient_id"])
            a_consultation = Consultation.query.filter_by(patient_id=patient_id).count() > 0
            hospitalisation = Hospitalisation(
                patient_id=patient_id,
                medecin_responsable_id=int(request.form["medecin_responsable_id"]),
                date_entree=datetime.strptime(request.form["date_entree"], "%Y-%m-%dT%H:%M"),
                motif=request.form["motif"].strip(),
                service=request.form.get("service"),
                chambre=request.form.get("chambre"),
            )
            hospitalisation.valider(a_consultation)
            db.session.add(hospitalisation)
            db.session.commit()
            flash("Hospitalisation enregistrée.", "success")
            return redirect(url_for("hospitalisations.liste"))
        except ValidationError as e:
            flash(str(e), "danger")
    return render_template("hospitalisations/form.html", patients=patients, medecins=medecins)


@hospitalisations_bp.route("/<int:hospitalisation_id>/suivi", methods=["POST"])
def ajouter_suivi(hospitalisation_id):
    hospitalisation = Hospitalisation.query.get_or_404(hospitalisation_id)
    suivi = SuiviQuotidien(
        hospitalisation_id=hospitalisation.id,
        horodatage=datetime.now(),
        temperature_c=request.form.get("temperature_c", type=float),
        tension_arterielle=request.form.get("tension_arterielle"),
        frequence_cardiaque=request.form.get("frequence_cardiaque", type=int),
        saturation_o2=request.form.get("saturation_o2", type=int),
        soins_prodigues=request.form.get("soins_prodigues"),
        etat_clinique=request.form.get("etat_clinique"),
        observations_infirmieres=request.form.get("observations_infirmieres"),
    )
    db.session.add(suivi)
    db.session.commit()
    flash("Suivi quotidien ajouté.", "success")
    return redirect(url_for("hospitalisations.liste"))


@hospitalisations_bp.route("/<int:hospitalisation_id>/sortie", methods=["POST"])
def enregistrer_sortie(hospitalisation_id):
    hospitalisation = Hospitalisation.query.get_or_404(hospitalisation_id)
    try:
        hospitalisation.enregistrer_sortie(
            mode_sortie=request.form["mode_sortie"],
            valide_par_medecin="valide_par_medecin" in request.form,
            recommandations=request.form.get("recommandations_suivi"),
        )
        db.session.commit()
        flash("Sortie enregistrée.", "success")
    except ValidationError as e:
        flash(str(e), "danger")
    return redirect(url_for("hospitalisations.liste"))
