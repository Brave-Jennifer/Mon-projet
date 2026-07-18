"""
Contrôleur Consultations : planification, agenda, suivi médical, historique.
La vérification de chevauchement et des règles métier est déléguée au modèle.
"""
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Consultation, Patient, Medecin, ValidationError

consultations_bp = Blueprint("consultations", __name__, url_prefix="/consultations")


@consultations_bp.route("/")
def agenda():
    medecin_id = request.args.get("medecin_id", type=int)
    motif = request.args.get("motif", "")
    date_debut = request.args.get("date_debut")
    date_fin = request.args.get("date_fin")

    query = Consultation.query
    if medecin_id:
        query = query.filter_by(medecin_id=medecin_id)
    if motif:
        query = query.filter(Consultation.motif.ilike(f"%{motif}%"))
    if date_debut:
        query = query.filter(Consultation.date_heure >= datetime.strptime(date_debut, "%Y-%m-%d"))
    if date_fin:
        query = query.filter(Consultation.date_heure <= datetime.strptime(date_fin, "%Y-%m-%d"))

    consultations = query.order_by(Consultation.date_heure).all()
    medecins = Medecin.query.all()
    return render_template("consultations/agenda.html", consultations=consultations,
                            medecins=medecins, medecin_id=medecin_id, motif=motif,
                            date_debut=date_debut, date_fin=date_fin)


@consultations_bp.route("/nouvelle", methods=["GET", "POST"])
def creer():
    patients = Patient.query.all()
    medecins = Medecin.query.all()
    if request.method == "POST":
        try:
            patient = Patient.query.get(request.form["patient_id"])
            if not patient:
                raise ValidationError("Le patient sélectionné n'existe pas.")
            medecin = Medecin.query.get(request.form["medecin_id"])
            if not medecin:
                raise ValidationError("Le médecin sélectionné n'existe pas.")

            date_heure = datetime.strptime(
                request.form["date_heure"], "%Y-%m-%dT%H:%M")

            consultation = Consultation(
                patient_id=patient.id,
                medecin_id=medecin.id,
                date_heure=date_heure,
                duree_minutes=int(request.form["duree_minutes"]),
                motif=request.form["motif"].strip(),
            )
            consultation.valider()

            # Règle métier : pas de double réservation pour un même médecin
            consultations_du_medecin = Consultation.query.filter_by(
                medecin_id=medecin.id).filter(
                Consultation.statut != "annulee").all()
            if any(consultation.chevauche(c) for c in consultations_du_medecin):
                raise ValidationError(
                    "Ce médecin a déjà une consultation sur ce créneau horaire.")

            # Règle métier : nombre maximal de consultations/jour pour un médecin
            from flask import current_app
            max_par_jour = current_app.config["MAX_CONSULTATIONS_PAR_JOUR_MEDECIN"]
            if medecin.nb_consultations_du_jour(date_heure.date()) >= max_par_jour:
                raise ValidationError(
                    f"Ce médecin a déjà atteint son quota de {max_par_jour} "
                    f"consultations pour cette journée.")

            db.session.add(consultation)
            db.session.commit()
            flash("Consultation planifiée.", "success")
            return redirect(url_for("consultations.agenda"))
        except ValidationError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Erreur : {e}", "danger")
    return render_template("consultations/form.html", patients=patients, medecins=medecins)


@consultations_bp.route("/<int:consultation_id>/suivi", methods=["GET", "POST"])
def suivi(consultation_id):
    consultation = Consultation.query.get_or_404(consultation_id)
    if request.method == "POST":
        try:
            medecin_id = int(request.form["medecin_id"])  # médecin connecté (simplifié)
            consultation.renseigner_suivi(
                medecin_id,
                symptomes=request.form.get("symptomes"),
                poids_kg=request.form.get("poids_kg", type=float),
                taille_cm=request.form.get("taille_cm", type=float),
                diagnostic=request.form.get("diagnostic"),
                traitement_prescrit=request.form.get("traitement_prescrit"),
                examens_complementaires=request.form.get("examens_complementaires"),
                notes_medecin=request.form.get("notes_medecin"),
            )
            db.session.commit()
            flash("Suivi médical enregistré.", "success")
            return redirect(url_for("patients.detail", patient_id=consultation.patient_id))
        except ValidationError as e:
            flash(str(e), "danger")
    return render_template("consultations/suivi.html", consultation=consultation)
