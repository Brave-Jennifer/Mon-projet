"""
Service d'analyse statistique du service de pédiatrie.
Utilise Pandas / NumPy pour transformer les données ORM en DataFrames
puis calculer les indicateurs demandés.
"""
from datetime import datetime

import numpy as np
import pandas as pd

from app.models import Patient, Consultation, Hospitalisation


class StatsService:
    """Regroupe les calculs statistiques. Ne contient aucune route ni template."""

    # ---------- Conversion ORM -> DataFrame ----------

    @staticmethod
    def _patients_df():
        patients = Patient.query.all()
        data = [{
            "id": p.id,
            "age": p.age,
            "sexe": p.sexe,
            "groupe_sanguin": p.groupe_sanguin,
            "antecedents": p.antecedents or "",
        } for p in patients]
        return pd.DataFrame(data)

    @staticmethod
    def _consultations_df():
        consultations = Consultation.query.all()
        data = [{
            "id": c.id,
            "patient_id": c.patient_id,
            "medecin_id": c.medecin_id,
            "date_heure": c.date_heure,
            "duree_minutes": c.duree_minutes,
            "motif": c.motif,
            "statut": c.statut,
            "diagnostic": c.diagnostic or "",
        } for c in consultations]
        return pd.DataFrame(data)

    @staticmethod
    def _hospitalisations_df():
        hospits = Hospitalisation.query.all()
        data = [{
            "id": h.id,
            "patient_id": h.patient_id,
            "motif": h.motif,
            "date_entree": h.date_entree,
            "date_sortie": h.date_sortie,
            "duree_jours": h.duree_jours,
        } for h in hospits]
        return pd.DataFrame(data)

    # ---------- Analyses ----------

    def pyramide_des_ages(self) -> dict:
        """Répartition des patients par tranche d'âge et sexe."""
        df = self._patients_df()
        if df.empty:
            return {"tranches": [], "hommes": [], "femmes": []}
        bins = [0, 2, 5, 10, 13, 16, 19]
        labels = ["0-2", "3-5", "6-10", "11-13", "14-16", "17-18"]
        df["tranche"] = pd.cut(df["age"], bins=bins, labels=labels, right=True, include_lowest=True)
        pivot = df.pivot_table(index="tranche", columns="sexe", values="id",
                                aggfunc="count", fill_value=0, observed=False)
        pivot = pivot.reindex(labels, fill_value=0)
        return {
            "tranches": labels,
            "hommes": pivot.get("M", pd.Series([0] * len(labels))).tolist(),
            "femmes": pivot.get("F", pd.Series([0] * len(labels))).tolist(),
        }

    def top_diagnostics(self, n: int = 10) -> dict:
        """Top N des diagnostics les plus fréquents parmi les consultations."""
        df = self._consultations_df()
        if df.empty or df["diagnostic"].eq("").all():
            return {"diagnostics": [], "effectifs": []}
        diag = df[df["diagnostic"] != ""]["diagnostic"].value_counts().head(n)
        return {"diagnostics": diag.index.tolist(), "effectifs": diag.values.tolist()}

    def evolution_consultations_mensuelle(self) -> dict:
        """Évolution du nombre de consultations mois par mois."""
        df = self._consultations_df()
        if df.empty:
            return {"mois": [], "effectifs": []}
        df["mois"] = pd.to_datetime(df["date_heure"]).dt.to_period("M").astype(str)
        counts = df.groupby("mois").size().sort_index()
        return {"mois": counts.index.tolist(), "effectifs": counts.values.tolist()}

    def taux_occupation_lits(self, nb_lits_total: int = 20) -> dict:
        """Taux d'occupation courant = hospitalisations en cours / lits disponibles."""
        df = self._hospitalisations_df()
        if df.empty:
            occupes = 0
        else:
            occupes = int(df["date_sortie"].isna().sum())
        taux = round(100 * occupes / nb_lits_total, 1) if nb_lits_total else 0.0
        return {"lits_total": nb_lits_total, "lits_occupes": occupes, "taux_pct": taux}

    def duree_moyenne_hospitalisation_par_pathologie(self) -> dict:
        df = self._hospitalisations_df()
        if df.empty:
            return {"pathologies": [], "duree_moyenne_jours": []}
        grouped = df.groupby("motif")["duree_jours"].mean().round(1).sort_values(ascending=False)
        return {"pathologies": grouped.index.tolist(), "duree_moyenne_jours": grouped.values.tolist()}

    def analyse_temps_attente(self) -> dict:
        """
        Estimation du temps d'attente = écart entre l'heure planifiée de la
        consultation et l'heure de début réelle. Ici on simplifie en supposant
        que les consultations 'en_cours'/'terminee' ont démarré à l'heure
        planifiée +/- une variabilité; à défaut de champ 'heure_debut_reelle'
        dédié, on documente cette limite dans le rapport de projet.
        """
        df = self._consultations_df()
        if df.empty:
            return {"duree_moyenne_minutes": 0, "nb_consultations": 0}
        return {
            "duree_moyenne_minutes": float(np.round(df["duree_minutes"].mean(), 1)),
            "nb_consultations": int(len(df)),
        }

    def correlation_age_pathologie(self) -> dict:
        """Nombre moyen de consultations par tranche d'âge (proxy de corrélation âge/pathologie)."""
        patients_df = self._patients_df()
        consult_df = self._consultations_df()
        if patients_df.empty or consult_df.empty:
            return {"tranches": [], "nb_consultations_moyen": []}
        merged = consult_df.merge(patients_df[["id", "age"]], left_on="patient_id", right_on="id",
                                   suffixes=("", "_patient"))
        bins = [0, 5, 10, 15, 19]
        labels = ["0-5", "6-10", "11-15", "16-18"]
        merged["tranche"] = pd.cut(merged["age"], bins=bins, labels=labels, include_lowest=True)
        grouped = merged.groupby("tranche", observed=False).size()
        return {"tranches": labels, "nb_consultations_moyen": grouped.reindex(labels, fill_value=0).tolist()}

    def indicateurs_cles(self) -> dict:
        """Indicateurs affichés sur la page d'accueil du dashboard."""
        nb_patients = Patient.query.count()
        nb_consultations = Consultation.query.count()
        occ = self.taux_occupation_lits()
        return {
            "nb_patients": nb_patients,
            "nb_consultations": nb_consultations,
            "lits_occupes": occ["lits_occupes"],
            "taux_occupation_pct": occ["taux_pct"],
            "date_actualisation": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
