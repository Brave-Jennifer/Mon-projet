"""Contrôleur Prescriptions : création et suivi de traitement."""
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Prescription, Consultation, ValidationError

prescriptions_bp = Blueprint("prescriptions", __name__, url_prefix="/prescriptions")


@prescriptions_bp.route("/consultation/<int:consultation_id>/nouvelle", methods=["GET", "POST"])
def creer(consultation_id):
    consultation = Consultation.query.get_or_404(consultation_id)
    if request.method == "POST":
        try:
            date_debut = datetime.strptime(request.form["date_debut"], "%Y-%m-%d").date()
            duree_jours = int(request.form["duree_jours"])
            prescription = Prescription(
                consultation_id=consultation.id,
                medicament=request.form["medicament"].strip(),
                dosage=request.form.get("dosage"),
                forme=request.form.get("forme"),
                frequence=request.form.get("frequence"),
                duree_jours=duree_jours,
                date_debut=date_debut,
                date_fin=date_debut + timedelta(days=duree_jours),
                medecin_prescripteur_id=consultation.medecin_id,
                exception_duree="exception_duree" in request.form,
            )
            prescription.valider()
            db.session.add(prescription)
            db.session.commit()
            flash("Prescription ajoutée.", "success")
            return redirect(url_for("patients.detail", patient_id=consultation.patient_id))
        except ValidationError as e:
            flash(str(e), "danger")
    return render_template("prescriptions/form.html", consultation=consultation)


@prescriptions_bp.route("/<int:prescription_id>/suivi", methods=["POST"])
def maj_suivi(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    prescription.observance = request.form.get("observance")
    prescription.effets_secondaires = request.form.get("effets_secondaires")
    prescription.renouvellement = "renouvellement" in request.form
    db.session.commit()
    flash("Suivi du traitement mis à jour.", "success")
    return redirect(url_for("patients.detail", patient_id=prescription.consultation.patient_id))
