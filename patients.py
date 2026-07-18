"""
Contrôleur Patients : orchestre les requêtes HTTP, délègue la validation
métier au modèle Patient et le traitement d'image au ImageService.
"""
from datetime import datetime

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, current_app)

from app.extensions import db
from app.models import Patient, ContactUrgence, Medecin, ValidationError
from app.services import ImageService

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")


@patients_bp.route("/")
def liste():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Patient.nom.ilike(like), Patient.prenom.ilike(like),
                                     Patient.identifiant_public.ilike(like)))
    patients = query.order_by(Patient.nom).all()
    return render_template("patients/list.html", patients=patients, q=q)


@patients_bp.route("/<int:patient_id>")
def detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("patients/detail.html", patient=patient)


@patients_bp.route("/nouveau", methods=["GET", "POST"])
def creer():
    medecins = Medecin.query.all()
    if request.method == "POST":
        try:
            patient = Patient(
                nom=request.form["nom"].strip(),
                prenom=request.form["prenom"].strip(),
                date_naissance=datetime.strptime(request.form["date_naissance"], "%Y-%m-%d").date(),
                sexe=request.form["sexe"],
                numero_secu=request.form.get("numero_secu"),
                groupe_sanguin=request.form.get("groupe_sanguin"),
                allergies=request.form.get("allergies"),
                antecedents=request.form.get("antecedents"),
                traitements_en_cours=request.form.get("traitements_en_cours"),
                medecin_referent_id=request.form.get("medecin_referent_id") or None,
                nom_parents=request.form.get("nom_parents"),
                telephone=request.form.get("telephone"),
                email=request.form.get("email"),
                adresse=request.form.get("adresse"),
            )
            patient.valider()

            contact_nom = request.form.get("contact_urgence_nom", "").strip()
            contact_tel = request.form.get("contact_urgence_telephone", "").strip()
            if not (contact_nom and contact_tel):
                raise ValidationError("Un patient doit avoir au moins un contact d'urgence.")
            contact = ContactUrgence(nom=contact_nom, lien=request.form.get("contact_urgence_lien"),
                                      telephone=contact_tel)
            patient.contacts_urgence.append(contact)

            photo = request.files.get("photo")
            if photo and photo.filename:
                image_service = ImageService(current_app.config["UPLOAD_FOLDER"])
                patient.photo_filename = image_service.traiter_photo_patient(photo)

            db.session.add(patient)
            db.session.commit()
            flash(f"Patient {patient.nom_complet} créé avec succès.", "success")
            return redirect(url_for("patients.detail", patient_id=patient.id))
        except ValidationError as e:
            flash(str(e), "danger")
        except Exception as e:
            current_app.logger.exception("Erreur lors de la création du patient")
            flash(f"Erreur inattendue : {e}", "danger")
    return render_template("patients/form.html", patient=None, medecins=medecins)


@patients_bp.route("/<int:patient_id>/modifier", methods=["GET", "POST"])
def modifier(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    medecins = Medecin.query.all()
    if request.method == "POST":
        try:
            patient.nom = request.form["nom"].strip()
            patient.prenom = request.form["prenom"].strip()
            patient.date_naissance = datetime.strptime(
                request.form["date_naissance"], "%Y-%m-%d").date()
            patient.sexe = request.form["sexe"]
            patient.groupe_sanguin = request.form.get("groupe_sanguin")
            patient.allergies = request.form.get("allergies")
            patient.antecedents = request.form.get("antecedents")
            patient.traitements_en_cours = request.form.get("traitements_en_cours")
            patient.medecin_referent_id = request.form.get("medecin_referent_id") or None
            patient.telephone = request.form.get("telephone")
            patient.email = request.form.get("email")
            patient.adresse = request.form.get("adresse")
            patient.valider()
            db.session.commit()
            flash("Patient mis à jour.", "success")
            return redirect(url_for("patients.detail", patient_id=patient.id))
        except ValidationError as e:
            db.session.rollback()
            flash(str(e), "danger")
    return render_template("patients/form.html", patient=patient, medecins=medecins)


@patients_bp.route("/<int:patient_id>/supprimer", methods=["POST"])
def supprimer(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash("Patient supprimé.", "info")
    return redirect(url_for("patients.liste"))
