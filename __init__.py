"""
Regroupe l'ensemble des modèles pour faciliter les imports
(ex: `from app.models import Patient, Medecin`).
"""
from app.models.patient import Patient, ContactUrgence, ValidationError
from app.models.personnel import Medecin, Infirmier, Secretaire
from app.models.consultation import Consultation, StatutConsultation
from app.models.prescription import Prescription
from app.models.hospitalisation import Hospitalisation, SuiviQuotidien

__all__ = [
    "Patient", "ContactUrgence", "ValidationError",
    "Medecin", "Infirmier", "Secretaire",
    "Consultation", "StatutConsultation",
    "Prescription",
    "Hospitalisation", "SuiviQuotidien",
]
