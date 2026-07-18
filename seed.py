"""
Script de génération de données de démonstration (patients, médecins,
consultations, prescriptions, hospitalisations) afin de pouvoir tester
l'application, l'API et le dashboard statistique immédiatement.

Usage :
    python seed.py
"""
import os
import random
from datetime import datetime, timedelta, date

from dotenv import load_dotenv
load_dotenv()

from faker import Faker

from app import create_app
from app.extensions import db
from app.models import (Patient, ContactUrgence, Medecin, Consultation,
                         Prescription, Hospitalisation, SuiviQuotidien)

fake = Faker("fr_FR")
random.seed(42)

SPECIALITES = ["Pédiatrie générale", "Néonatalogie", "Pneumo-pédiatrie", "Pédiatrie urgences"]
MOTIFS = ["Fièvre", "Toux persistante", "Contrôle de croissance", "Vaccination",
          "Douleurs abdominales", "Éruption cutanée", "Bilan de routine", "Otite"]
DIAGNOSTICS = ["Angine virale", "Bronchiolite", "Otite moyenne aiguë", "Gastro-entérite",
               "Varicelle", "Asthme léger", "RAS - bonne santé", "Rhinopharyngite"]


def run():
    app = create_app("development")
    with app.app_context():
        db.drop_all()
        db.create_all()

        medecins = []
        for _ in range(6):
            m = Medecin(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                specialite=random.choice(SPECIALITES),
                numero_ordre=f"ORD-{random.randint(10000, 99999)}",
            )
            db.session.add(m)
            medecins.append(m)
        db.session.commit()

        patients = []
        for _ in range(40):
            naissance = fake.date_of_birth(minimum_age=0, maximum_age=18)
            sexe = random.choice(["M", "F"])
            p = Patient(
                nom=fake.last_name(),
                prenom=fake.first_name_male() if sexe == "M" else fake.first_name_female(),
                date_naissance=naissance,
                sexe=sexe,
                groupe_sanguin=random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+"]),
                allergies=random.choice(["Aucune", "Pénicilline", "Arachides", "Aucune", "Aucune"]),
                antecedents=random.choice(["RAS", "Asthme", "RAS", "Prématurité"]),
                medecin_referent_id=random.choice(medecins).id,
                nom_parents=fake.name(),
                telephone=fake.phone_number(),
                email=fake.email(),
                adresse=fake.address(),
            )
            p.contacts_urgence.append(ContactUrgence(
                nom=fake.name(), lien=random.choice(["mère", "père", "tuteur"]),
                telephone=fake.phone_number()))
            db.session.add(p)
            patients.append(p)
        db.session.commit()

        # Consultations réparties sur les 12 derniers mois
        consultations = []
        for _ in range(150):
            patient = random.choice(patients)
            medecin = random.choice(medecins)
            jours_avant = random.randint(0, 365)
            date_heure = datetime.now() - timedelta(days=jours_avant,
                                                      hours=random.randint(0, 8))
            date_heure = date_heure.replace(minute=random.choice([0, 15, 30, 45]), second=0, microsecond=0)
            c = Consultation(
                patient_id=patient.id,
                medecin_id=medecin.id,
                date_heure=date_heure,
                duree_minutes=random.choice([15, 30, 60]),
                motif=random.choice(MOTIFS),
                statut="terminee",
                diagnostic=random.choice(DIAGNOSTICS),
                poids_kg=round(random.uniform(3, 60), 1),
                taille_cm=round(random.uniform(45, 170), 1),
                notes_medecin="RAS",
            )
            db.session.add(c)
            consultations.append(c)
        db.session.commit()

        # Prescriptions pour une partie des consultations
        for c in random.sample(consultations, 60):
            debut = c.date_heure.date()
            duree = random.choice([5, 7, 10, 14])
            db.session.add(Prescription(
                consultation_id=c.id,
                medicament=random.choice(["Paracétamol", "Amoxicilline", "Ibuprofène", "Sirop antitussif"]),
                dosage=random.choice(["250 mg", "500 mg", "5 mL"]),
                forme=random.choice(["comprimé", "sirop", "suppositoire"]),
                frequence=random.choice(["3 fois/jour", "2 fois/jour", "1 fois/jour"]),
                duree_jours=duree,
                date_debut=debut,
                date_fin=debut + timedelta(days=duree),
                medecin_prescripteur_id=c.medecin_id,
                observance=random.choice(["bonne", "partielle"]),
            ))
        db.session.commit()

        # Hospitalisations pour quelques patients ayant déjà une consultation
        patients_avec_consult = list({c.patient_id for c in consultations})
        for patient_id in random.sample(patients_avec_consult, 8):
            entree = datetime.now() - timedelta(days=random.randint(1, 60))
            sortie = entree + timedelta(days=random.randint(1, 10)) if random.random() > 0.3 else None
            h = Hospitalisation(
                patient_id=patient_id,
                medecin_responsable_id=random.choice(medecins).id,
                date_entree=entree,
                motif=random.choice(["Bronchiolite sévère", "Déshydratation", "Surveillance post-opératoire",
                                      "Pneumonie", "Crise d'asthme"]),
                service="Pédiatrie",
                chambre=f"P-{random.randint(1, 20)}",
                date_sortie=sortie,
                mode_sortie="guerison" if sortie else None,
                sortie_validee_par_medecin=bool(sortie),
            )
            db.session.add(h)
            db.session.flush()
            for j in range(3):
                db.session.add(SuiviQuotidien(
                    hospitalisation_id=h.id,
                    horodatage=entree + timedelta(days=j),
                    temperature_c=round(random.uniform(36.5, 39.0), 1),
                    tension_arterielle=f"{random.randint(90,120)}/{random.randint(55,80)}",
                    frequence_cardiaque=random.randint(70, 130),
                    saturation_o2=random.randint(94, 100),
                    etat_clinique=random.choice(["stable", "amélioration", "surveillance"]),
                    observations_infirmieres="RAS",
                ))
        db.session.commit()

        print(f"Données générées : {len(patients)} patients, {len(medecins)} médecins, "
              f"{len(consultations)} consultations.")


if __name__ == "__main__":
    run()
