from datetime import date, datetime, timedelta

import pytest

from app.models import (Patient, ContactUrgence, Medecin, Consultation,
                         Prescription, ValidationError)


def _patient_valide(**overrides):
    donnees = dict(
        nom="Dupont", prenom="Léo",
        date_naissance=date.today().replace(year=date.today().year - 8),
        sexe="M",
    )
    donnees.update(overrides)
    return Patient(**donnees)


def test_patient_age_hors_limite_leve_erreur():
    """Un patient de plus de 18 ans doit être rejeté (règle métier 0-18 ans)."""
    patient = _patient_valide(date_naissance=date(1990, 1, 1))
    with pytest.raises(ValidationError):
        patient.valider()


def test_patient_age_valide_est_accepte():
    patient = _patient_valide()
    assert patient.valider() is True
    assert 0 <= patient.age <= 18


def test_patient_necessite_contact_urgence(db):
    """Un patient sans contact d'urgence ne doit pas être considéré complet."""
    patient = _patient_valide()
    db.session.add(patient)
    db.session.commit()
    assert patient.a_un_contact_urgence() is False

    patient.contacts_urgence.append(
        ContactUrgence(nom="Marie Dupont", lien="mère", telephone="0600000000"))
    db.session.commit()
    assert patient.a_un_contact_urgence() is True


def test_consultation_duree_invalide_leve_erreur():
    consultation = Consultation(
        patient_id=1, medecin_id=1, date_heure=datetime.now(),
        duree_minutes=45,  # durée non autorisée
        motif="Contrôle",
    )
    with pytest.raises(ValidationError):
        consultation.valider()


def test_consultation_chevauchement_detecte():
    """Deux consultations qui se recouvrent dans le temps doivent être détectées."""
    debut = datetime(2026, 1, 10, 9, 0)
    c1 = Consultation(patient_id=1, medecin_id=1, date_heure=debut,
                       duree_minutes=30, motif="Contrôle")
    c2 = Consultation(patient_id=2, medecin_id=1, date_heure=debut + timedelta(minutes=15),
                       duree_minutes=30, motif="Vaccination")
    c3 = Consultation(patient_id=2, medecin_id=1, date_heure=debut + timedelta(minutes=30),
                       duree_minutes=30, motif="Vaccination")
    assert c1.chevauche(c2) is True
    assert c1.chevauche(c3) is False


def test_prescription_duree_maximale_depassee():
    prescription = Prescription(
        consultation_id=1, medicament="Antibiotique", duree_jours=120,
        date_debut=date.today(), medecin_prescripteur_id=1,
    )
    with pytest.raises(ValidationError):
        prescription.valider()

    prescription.exception_duree = True
    assert prescription.valider() is True


def test_medecin_nb_consultations_du_jour():
    medecin = Medecin(nom="Martin", prenom="Claire", specialite="Pédiatrie générale",
                       numero_ordre="ORD-1")
    jour = date(2026, 3, 1)
    medecin.consultations = [
        Consultation(patient_id=1, date_heure=datetime(2026, 3, 1, 9, 0),
                     duree_minutes=30, motif="A"),
        Consultation(patient_id=2, date_heure=datetime(2026, 3, 1, 10, 0),
                     duree_minutes=30, motif="B"),
        Consultation(patient_id=3, date_heure=datetime(2026, 3, 2, 9, 0),
                     duree_minutes=30, motif="C"),
    ]
    assert medecin.nb_consultations_du_jour(jour) == 2
