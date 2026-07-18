"""
Modèles du personnel médical : Medecin, Infirmier, Secretaire.
"""
from app.extensions import db
from app.models.patient import ValidationError


class Medecin(db.Model):
    __tablename__ = "medecins"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    specialite = db.Column(db.String(100), nullable=False)
    numero_ordre = db.Column(db.String(30), unique=True, nullable=False)

    # Disponibilités stockées en JSON simplifié : {"lundi": ["08:00-12:00", ...], ...}
    disponibilites = db.Column(db.JSON, nullable=True, default=dict)

    patients = db.relationship("Patient", back_populates="medecin_referent")
    consultations = db.relationship("Consultation", back_populates="medecin")

    @property
    def nom_complet(self) -> str:
        return f"Dr. {self.prenom} {self.nom}"

    def valider(self):
        if not self.nom or not self.prenom:
            raise ValidationError("Nom et prénom du médecin obligatoires.")
        if not self.specialite:
            raise ValidationError("La spécialité est obligatoire.")
        if not self.numero_ordre:
            raise ValidationError("Le numéro d'ordre est obligatoire.")
        return True

    def nb_consultations_du_jour(self, jour):
        return sum(1 for c in self.consultations if c.date_heure.date() == jour)

    def __repr__(self):
        return f"<Medecin {self.nom_complet}>"


class Infirmier(db.Model):
    __tablename__ = "infirmiers"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    qualifications = db.Column(db.String(200), nullable=True)
    service_affectation = db.Column(db.String(100), nullable=True)

    def valider(self):
        if not self.nom or not self.prenom:
            raise ValidationError("Nom et prénom de l'infirmier obligatoires.")
        return True

    def __repr__(self):
        return f"<Infirmier {self.prenom} {self.nom}>"


class Secretaire(db.Model):
    __tablename__ = "secretaires"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    responsabilites = db.Column(db.String(250), nullable=True)

    def valider(self):
        if not self.nom or not self.prenom:
            raise ValidationError("Nom et prénom du secrétaire obligatoires.")
        return True

    def __repr__(self):
        return f"<Secretaire {self.prenom} {self.nom}>"
