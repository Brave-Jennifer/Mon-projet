"""
Modèle Consultation : planification + suivi médical.
"""
from datetime import timedelta
import enum

from app.extensions import db
from app.models.patient import ValidationError


class StatutConsultation(str, enum.Enum):
    PLANIFIEE = "planifiee"
    CONFIRMEE = "confirmee"
    EN_COURS = "en_cours"
    TERMINEE = "terminee"
    ANNULEE = "annulee"


class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey("medecins.id"), nullable=False)

    date_heure = db.Column(db.DateTime, nullable=False)
    duree_minutes = db.Column(db.Integer, nullable=False, default=30)
    motif = db.Column(db.String(250), nullable=False)
    statut = db.Column(db.String(20), nullable=False, default=StatutConsultation.PLANIFIEE.value)

    # Suivi médical (rempli uniquement par le médecin)
    symptomes = db.Column(db.Text, nullable=True)
    poids_kg = db.Column(db.Float, nullable=True)
    taille_cm = db.Column(db.Float, nullable=True)
    diagnostic = db.Column(db.Text, nullable=True)
    traitement_prescrit = db.Column(db.Text, nullable=True)
    examens_complementaires = db.Column(db.Text, nullable=True)
    notes_medecin = db.Column(db.Text, nullable=True)

    patient = db.relationship("Patient", back_populates="consultations")
    medecin = db.relationship("Medecin", back_populates="consultations")
    prescriptions = db.relationship("Prescription", back_populates="consultation",
                                     cascade="all, delete-orphan")

    DUREES_AUTORISEES = (15, 30, 60)

    @property
    def date_fin(self):
        return self.date_heure + timedelta(minutes=self.duree_minutes)

    def valider(self):
        if self.duree_minutes not in self.DUREES_AUTORISEES:
            raise ValidationError(
                f"La durée doit être l'une des valeurs suivantes (minutes) : "
                f"{self.DUREES_AUTORISEES}."
            )
        if not self.motif:
            raise ValidationError("Le motif de consultation est obligatoire.")
        if not self.patient_id:
            raise ValidationError("La consultation doit être associée à un patient existant.")
        if not self.medecin_id:
            raise ValidationError("La consultation doit être associée à un médecin existant.")
        return True

    def chevauche(self, autre: "Consultation") -> bool:
        """Vrai si deux consultations du même médecin se chevauchent dans le temps."""
        return self.date_heure < autre.date_fin and autre.date_heure < self.date_fin

    def renseigner_suivi(self, medecin_id: int, **kwargs):
        """
        Seul le médecin affecté à la consultation peut renseigner le suivi médical.
        """
        if medecin_id != self.medecin_id:
            raise ValidationError("Seul le médecin de la consultation peut renseigner le suivi.")
        for champ in ("symptomes", "poids_kg", "taille_cm", "diagnostic",
                      "traitement_prescrit", "examens_complementaires", "notes_medecin"):
            if champ in kwargs:
                setattr(self, champ, kwargs[champ])
        self.statut = StatutConsultation.TERMINEE.value

    def __repr__(self):
        return f"<Consultation #{self.id} {self.date_heure}>"
