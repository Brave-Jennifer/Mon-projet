"""
Modèle Prescription : médicaments prescrits et suivi du traitement.
"""
from app.extensions import db
from app.models.patient import ValidationError

DUREE_MAX_TRAITEMENT_JOURS = 90


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey("consultations.id"), nullable=False)

    medicament = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(80), nullable=True)
    forme = db.Column(db.String(50), nullable=True)  # comprimé, sirop, etc.

    frequence = db.Column(db.String(80), nullable=True)  # ex: "3 fois/jour"
    duree_jours = db.Column(db.Integer, nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=True)

    medecin_prescripteur_id = db.Column(db.Integer, db.ForeignKey("medecins.id"), nullable=False)

    # Suivi
    observance = db.Column(db.String(20), nullable=True)  # bonne / partielle / mauvaise
    effets_secondaires = db.Column(db.Text, nullable=True)
    renouvellement = db.Column(db.Boolean, default=False)
    exception_duree = db.Column(db.Boolean, default=False)  # dérogation explicite à la durée max

    consultation = db.relationship("Consultation", back_populates="prescriptions")
    medecin_prescripteur = db.relationship("Medecin")

    def valider(self):
        if not self.medicament:
            raise ValidationError("Le nom du médicament est obligatoire.")
        if not self.consultation_id:
            raise ValidationError("Une prescription doit être associée à une consultation.")
        if self.duree_jours > DUREE_MAX_TRAITEMENT_JOURS and not self.exception_duree:
            raise ValidationError(
                f"La durée du traitement ({self.duree_jours} j) dépasse la limite de "
                f"{DUREE_MAX_TRAITEMENT_JOURS} jours. Cochez 'exception' si justifié."
            )
        return True

    def __repr__(self):
        return f"<Prescription {self.medicament} ({self.duree_jours}j)>"
