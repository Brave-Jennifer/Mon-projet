from datetime import date, datetime

from app.models import Patient, Medecin, Consultation, ContactUrgence
from app.services import StatsService


def _creer_jeu_de_donnees(db):
    medecin = Medecin(nom="Petit", prenom="Sophie", specialite="Pédiatrie générale",
                       numero_ordre="ORD-99")
    db.session.add(medecin)
    db.session.commit()

    patient1 = Patient(nom="A", prenom="Enfant1", date_naissance=date(2018, 1, 1), sexe="M")
    patient1.contacts_urgence.append(ContactUrgence(nom="Parent1", telephone="0600000001"))
    patient2 = Patient(nom="B", prenom="Enfant2", date_naissance=date(2010, 6, 1), sexe="F")
    patient2.contacts_urgence.append(ContactUrgence(nom="Parent2", telephone="0600000002"))
    db.session.add_all([patient1, patient2])
    db.session.commit()

    db.session.add(Consultation(
        patient_id=patient1.id, medecin_id=medecin.id, date_heure=datetime(2026, 1, 15, 9, 0),
        duree_minutes=30, motif="Contrôle", statut="terminee", diagnostic="RAS",
    ))
    db.session.add(Consultation(
        patient_id=patient2.id, medecin_id=medecin.id, date_heure=datetime(2026, 2, 10, 10, 0),
        duree_minutes=15, motif="Vaccination", statut="terminee", diagnostic="RAS",
    ))
    db.session.commit()
    return medecin, patient1, patient2


def test_stats_indicateurs_cles(db):
    """Le service de statistiques doit refléter les données réellement en base."""
    _creer_jeu_de_donnees(db)
    service = StatsService()
    indicateurs = service.indicateurs_cles()
    assert indicateurs["nb_patients"] == 2
    assert indicateurs["nb_consultations"] == 2


def test_stats_evolution_consultations_mensuelle(db):
    _creer_jeu_de_donnees(db)
    service = StatsService()
    resultat = service.evolution_consultations_mensuelle()
    assert resultat["mois"] == ["2026-01", "2026-02"]
    assert resultat["effectifs"] == [1, 1]


def test_stats_pyramide_des_ages_vide_sans_donnees(db):
    """Sans aucun patient, la pyramide des âges ne doit pas lever d'erreur."""
    service = StatsService()
    resultat = service.pyramide_des_ages()
    assert resultat["tranches"] == []


def test_api_liste_patients_retourne_200(client, db):
    _creer_jeu_de_donnees(db)
    response = client.get("/api/patients")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_api_patient_inexistant_retourne_404(client, db):
    response = client.get("/api/patients/999")
    assert response.status_code == 404
    assert "erreur" in response.get_json()
