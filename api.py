"""
API REST de l'application. Toutes les réponses sont en JSON, avec des
codes de statut HTTP appropriés (200, 201, 400, 404, 500) et des messages
d'erreur explicites.
"""
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app

from app.extensions import db
from app.models import Patient, Consultation, Medecin, ValidationError
from app.services import StatsService, VizService

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------- Helpers de sérialisation ----------

def patient_to_dict(p: Patient) -> dict:
    return {
        "id": p.id,
        "identifiant_public": p.identifiant_public,
        "nom": p.nom,
        "prenom": p.prenom,
        "date_naissance": p.date_naissance.isoformat(),
        "age": p.age,
        "sexe": p.sexe,
        "groupe_sanguin": p.groupe_sanguin,
        "allergies": p.allergies,
        "medecin_referent_id": p.medecin_referent_id,
        "telephone": p.telephone,
        "email": p.email,
    }


def consultation_to_dict(c: Consultation) -> dict:
    return {
        "id": c.id,
        "patient_id": c.patient_id,
        "medecin_id": c.medecin_id,
        "date_heure": c.date_heure.isoformat(),
        "duree_minutes": c.duree_minutes,
        "motif": c.motif,
        "statut": c.statut,
        "diagnostic": c.diagnostic,
    }


def medecin_to_dict(m: Medecin) -> dict:
    return {
        "id": m.id,
        "nom": m.nom,
        "prenom": m.prenom,
        "specialite": m.specialite,
        "numero_ordre": m.numero_ordre,
        "disponibilites": m.disponibilites,
    }


# ---------- Gestion d'erreurs uniforme ----------

@api_bp.errorhandler(ValidationError)
def handle_validation_error(err):
    return jsonify({"erreur": str(err)}), 400


@api_bp.errorhandler(404)
def handle_404(err):
    return jsonify({"erreur": "Ressource non trouvée."}), 404


@api_bp.errorhandler(500)
def handle_500(err):
    current_app.logger.exception("Erreur serveur API")
    return jsonify({"erreur": "Erreur interne du serveur."}), 500


# ---------- Patients ----------

@api_bp.route("/patients", methods=["GET"])
def get_patients():
    patients = Patient.query.all()
    return jsonify([patient_to_dict(p) for p in patients]), 200


@api_bp.route("/patients/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"erreur": f"Patient {patient_id} introuvable."}), 404
    return jsonify(patient_to_dict(patient)), 200


@api_bp.route("/patients", methods=["POST"])
def create_patient():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Corps JSON manquant ou invalide."}), 400
    try:
        patient = Patient(
            nom=payload.get("nom", "").strip(),
            prenom=payload.get("prenom", "").strip(),
            date_naissance=datetime.strptime(payload["date_naissance"], "%Y-%m-%d").date(),
            sexe=payload.get("sexe"),
            groupe_sanguin=payload.get("groupe_sanguin"),
            allergies=payload.get("allergies"),
        )
        patient.valider()
        db.session.add(patient)
        db.session.commit()
        return jsonify(patient_to_dict(patient)), 201
    except (KeyError, ValueError) as e:
        return jsonify({"erreur": f"Champ manquant ou invalide : {e}"}), 400


@api_bp.route("/patients/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"erreur": f"Patient {patient_id} introuvable."}), 404
    payload = request.get_json(silent=True) or {}
    for champ in ("nom", "prenom", "sexe", "groupe_sanguin", "allergies", "telephone", "email"):
        if champ in payload:
            setattr(patient, champ, payload[champ])
    if "date_naissance" in payload:
        patient.date_naissance = datetime.strptime(payload["date_naissance"], "%Y-%m-%d").date()
    patient.valider()
    db.session.commit()
    return jsonify(patient_to_dict(patient)), 200


@api_bp.route("/patients/<int:patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"erreur": f"Patient {patient_id} introuvable."}), 404
    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": "Patient supprimé."}), 200


# ---------- Consultations ----------

@api_bp.route("/consultations", methods=["GET"])
def get_consultations():
    query = Consultation.query
    medecin_id = request.args.get("medecin_id", type=int)
    patient_id = request.args.get("patient_id", type=int)
    statut = request.args.get("statut")
    if medecin_id:
        query = query.filter_by(medecin_id=medecin_id)
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if statut:
        query = query.filter_by(statut=statut)
    consultations = query.order_by(Consultation.date_heure).all()
    return jsonify([consultation_to_dict(c) for c in consultations]), 200


@api_bp.route("/consultations/<int:consultation_id>", methods=["GET"])
def get_consultation(consultation_id):
    c = Consultation.query.get(consultation_id)
    if not c:
        return jsonify({"erreur": f"Consultation {consultation_id} introuvable."}), 404
    return jsonify(consultation_to_dict(c)), 200


@api_bp.route("/consultations", methods=["POST"])
def create_consultation():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Corps JSON manquant ou invalide."}), 400
    try:
        if not Patient.query.get(payload.get("patient_id")):
            return jsonify({"erreur": "Le patient indiqué n'existe pas."}), 400
        if not Medecin.query.get(payload.get("medecin_id")):
            return jsonify({"erreur": "Le médecin indiqué n'existe pas."}), 400

        consultation = Consultation(
            patient_id=payload["patient_id"],
            medecin_id=payload["medecin_id"],
            date_heure=datetime.strptime(payload["date_heure"], "%Y-%m-%dT%H:%M:%S"),
            duree_minutes=payload.get("duree_minutes", 30),
            motif=payload.get("motif", "").strip(),
        )
        consultation.valider()

        existantes = Consultation.query.filter_by(medecin_id=consultation.medecin_id).all()
        if any(consultation.chevauche(c) for c in existantes):
            return jsonify({"erreur": "Créneau déjà occupé pour ce médecin."}), 400

        db.session.add(consultation)
        db.session.commit()
        return jsonify(consultation_to_dict(consultation)), 201
    except (KeyError, ValueError) as e:
        return jsonify({"erreur": f"Champ manquant ou invalide : {e}"}), 400


@api_bp.route("/consultations/<int:consultation_id>", methods=["PUT"])
def update_consultation(consultation_id):
    c = Consultation.query.get(consultation_id)
    if not c:
        return jsonify({"erreur": f"Consultation {consultation_id} introuvable."}), 404
    payload = request.get_json(silent=True) or {}
    for champ in ("motif", "statut", "diagnostic", "notes_medecin"):
        if champ in payload:
            setattr(c, champ, payload[champ])
    db.session.commit()
    return jsonify(consultation_to_dict(c)), 200


# ---------- Médecins ----------

@api_bp.route("/medecins", methods=["GET"])
def get_medecins():
    medecins = Medecin.query.all()
    return jsonify([medecin_to_dict(m) for m in medecins]), 200


@api_bp.route("/medecins/<int:medecin_id>", methods=["GET"])
def get_medecin(medecin_id):
    m = Medecin.query.get(medecin_id)
    if not m:
        return jsonify({"erreur": f"Médecin {medecin_id} introuvable."}), 404
    return jsonify(medecin_to_dict(m)), 200


# ---------- Statistiques ----------

@api_bp.route("/stats", methods=["GET"])
def get_stats():
    service = StatsService()
    return jsonify({
        "indicateurs_cles": service.indicateurs_cles(),
        "pyramide_ages": service.pyramide_des_ages(),
        "top_diagnostics": service.top_diagnostics(),
        "evolution_consultations": service.evolution_consultations_mensuelle(),
        "occupation_lits": service.taux_occupation_lits(),
        "duree_hospitalisation": service.duree_moyenne_hospitalisation_par_pathologie(),
    }), 200


@api_bp.route("/stats/graphiques", methods=["GET"])
def get_graphiques():
    viz_service = VizService(current_app.config["GRAPH_FOLDER"])
    fichiers = viz_service.generer_tous_les_graphiques()
    urls = {cle: f"/static/graphs/{nom}" for cle, nom in fichiers.items()}
    return jsonify(urls), 200
