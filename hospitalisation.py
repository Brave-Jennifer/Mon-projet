"""
Modèle Hospitalisation : admission, suivi quotidien, sortie.
"""
from app.extensions import db
from app.models.patient import ValidationError


class Hospitalisation(db.Model):
    __tablename__ = "hospitalisations"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    medecin_responsable_id = db.Column(db.Integer, db.ForeignKey("medecins.id"), nullable=False)

    date_entree = db.Column(db.DateTime, nullable=False)
    motif = db.Column(db.String(250), nullable=False)
    service = db.Column(db.String(100), nullable=True)
    chambre = db.Column(db.String(20), nullable=True)

    date_sortie = db.Column(db.DateTime, nullable=True)
    mode_sortie = db.Column(db.String(30), nullable=True)  # guerison / transfert / deces
    recommandations_suivi = db.Column(db.Text, nullable=True)
    sortie_validee_par_medecin = db.Column(db.Boolean, default=False)

    patient = db.relationship("Patient", back_populates="hospitalisations")
    medecin_responsable = db.relationship("Medecin")
    suivis_quotidiens = db.relationship("SuiviQuotidien", back_populates="hospitalisation",
                                         cascade="all, delete-orphan")

    def valider(self, patient_a_consultation_prealable: bool):
        if not patient_a_consultation_prealable:
            raise ValidationError(
                "Un patient ne peut être hospitalisé que s'il a une consultation préalable."
            )
        if not self.motif:
            raise ValidationError("Le motif d'hospitalisation est obligatoire.")
        return True

    def enregistrer_sortie(self, mode_sortie: str, valide_par_medecin: bool, recommandations=None):
        if not valide_par_medecin:
            raise ValidationError("La sortie doit être validée par un médecin.")
        self.mode_sortie = mode_sortie
        self.sortie_validee_par_medecin = True
        self.recommandations_suivi = recommandations
        from datetime import datetime
        self.date_sortie = datetime.now()

    @property
    def duree_jours(self):
        fin = self.date_sortie or __import__("datetime").datetime.now()
        return (fin - self.date_entree).days

    @property
    def en_cours(self):
        return self.date_sortie is None

    def __repr__(self):
        return f"<Hospitalisation patient={self.patient_id} chambre={self.chambre}>"


class SuiviQuotidien(db.Model):
    """Paramètres vitaux et observations infirmières, au moins 1x/jour."""
    __tablename__ = "suivis_quotidiens"

    id = db.Column(db.Integer, primary_key=True)
    hospitalisation_id = db.Column(db.Integer, db.ForeignKey("hospitalisations.id"), nullable=False)
    horodatage = db.Column(db.DateTime, nullable=False)

    temperature_c = db.Column(db.Float, nullable=True)
    tension_arterielle = db.Column(db.String(20), nullable=True)  # ex "110/70"
    frequence_cardiaque = db.Column(db.Integer, nullable=True)
    saturation_o2 = db.Column(db.Integer, nullable=True)

    soins_prodigues = db.Column(db.Text, nullable=True)
    etat_clinique = db.Column(db.String(50), nullable=True)
    observations_infirmieres = db.Column(db.Text, nullable=True)

    hospitalisation = db.relationship("Hospitalisation", back_populates="suivis_quotidiens")

    def __repr__(self):
        return f"<SuiviQuotidien {self.horodatage}>"
