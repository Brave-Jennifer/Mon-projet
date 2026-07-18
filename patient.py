"""
Modèle Patient : encapsule les données du dossier patient ainsi que les
règles métier associées (âge 0-18 ans, contact d'urgence obligatoire).
"""
from datetime import date
import uuid

from app.extensions import db


class ValidationError(Exception):
    """Levée quand une règle métier n'est pas respectée."""
    pass


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    identifiant_public = db.Column(db.String(36), unique=True, nullable=False,
                                    default=lambda: str(uuid.uuid4())[:8].upper())

    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    date_naissance = db.Column(db.Date, nullable=False)
    sexe = db.Column(db.String(1), nullable=False)  # 'M' ou 'F'
    numero_secu = db.Column(db.String(20), nullable=True)

    # Informations médicales
    groupe_sanguin = db.Column(db.String(5), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    antecedents = db.Column(db.Text, nullable=True)
    traitements_en_cours = db.Column(db.Text, nullable=True)
    medecin_referent_id = db.Column(db.Integer, db.ForeignKey("medecins.id"), nullable=True)

    # Informations familiales
    nom_parents = db.Column(db.String(200), nullable=True)
    telephone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    adresse = db.Column(db.String(250), nullable=True)

    photo_filename = db.Column(db.String(255), nullable=True)

    date_creation = db.Column(db.DateTime, server_default=db.func.now())

    medecin_referent = db.relationship("Medecin", back_populates="patients")
    contacts_urgence = db.relationship("ContactUrgence", backref="patient",
                                        cascade="all, delete-orphan")
    consultations = db.relationship("Consultation", back_populates="patient",
                                     cascade="all, delete-orphan")
    hospitalisations = db.relationship("Hospitalisation", back_populates="patient",
                                        cascade="all, delete-orphan")

    # ---------- Règles métier ----------

    @staticmethod
    def calculer_age(date_naissance: date, aujourdhui: date = None) -> int:
        aujourdhui = aujourdhui or date.today()
        age = aujourdhui.year - date_naissance.year
        if (aujourdhui.month, aujourdhui.day) < (date_naissance.month, date_naissance.day):
            age -= 1
        return age

    @property
    def age(self) -> int:
        return self.calculer_age(self.date_naissance)

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"

    def valider(self):
        """Vérifie les contraintes métier avant sauvegarde. Lève ValidationError sinon."""
        if not self.nom or not self.prenom:
            raise ValidationError("Le nom et le prénom sont obligatoires.")
        if not self.date_naissance:
            raise ValidationError("La date de naissance est obligatoire.")
        age = self.calculer_age(self.date_naissance)
        if age < 0 or age > 18:
            raise ValidationError(
                f"Le patient doit avoir entre 0 et 18 ans (âge calculé : {age})."
            )
        if self.sexe not in ("M", "F"):
            raise ValidationError("Le sexe doit être 'M' ou 'F'.")
        # Un patient doit avoir au moins un contact d'urgence : vérifié séparément
        # après ajout des contacts (voir PatientService), car la relation n'est
        # peuplée qu'une fois les objets liés créés.
        return True

    def a_un_contact_urgence(self) -> bool:
        return len(self.contacts_urgence) >= 1

    def __repr__(self):
        return f"<Patient {self.identifiant_public} {self.nom_complet}>"


class ContactUrgence(db.Model):
    """Personne à contacter en cas d'urgence pour un patient donné."""
    __tablename__ = "contacts_urgence"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    lien = db.Column(db.String(50), nullable=True)  # ex: père, mère, tuteur
    telephone = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"<ContactUrgence {self.nom} ({self.lien})>"
