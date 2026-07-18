"""
Service de visualisation : génère les graphiques (Matplotlib/Seaborn) demandés
par le cahier des charges et les enregistre dans app/static/graphs/.
"""
import os

import matplotlib
matplotlib.use("Agg")  # rendu serveur, sans affichage graphique
import matplotlib.pyplot as plt
import seaborn as sns

from app.services.stats_service import StatsService

sns.set_theme(style="whitegrid")


class VizService:
    def __init__(self, graph_folder: str):
        self.graph_folder = graph_folder
        os.makedirs(self.graph_folder, exist_ok=True)
        self.stats = StatsService()

    def _save(self, fig, filename: str) -> str:
        path = os.path.join(self.graph_folder, filename)
        fig.savefig(path, bbox_inches="tight", dpi=110)
        plt.close(fig)
        return filename

    def pyramide_des_ages(self) -> str:
        data = self.stats.pyramide_des_ages()
        fig, ax = plt.subplots(figsize=(7, 5))
        y = range(len(data["tranches"]))
        ax.barh(y, [-v for v in data["hommes"]], color="#4C72B0", label="Garçons")
        ax.barh(y, data["femmes"], color="#DD8452", label="Filles")
        ax.set_yticks(list(y))
        ax.set_yticklabels(data["tranches"])
        ax.set_xlabel("Nombre de patients")
        ax.set_title("Pyramide des âges des patients")
        ax.axvline(0, color="black", linewidth=0.8)
        ax.legend()
        return self._save(fig, "pyramide_ages.png")

    def top_diagnostics(self) -> str:
        data = self.stats.top_diagnostics()
        fig, ax = plt.subplots(figsize=(8, 5))
        if data["diagnostics"]:
            sns.barplot(x=data["effectifs"], y=data["diagnostics"], ax=ax, palette="viridis",
                        hue=data["diagnostics"], legend=False)
        ax.set_title("Top 10 des diagnostics")
        ax.set_xlabel("Nombre de cas")
        ax.set_ylabel("Diagnostic")
        return self._save(fig, "top_diagnostics.png")

    def evolution_consultations(self) -> str:
        data = self.stats.evolution_consultations_mensuelle()
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(data["mois"], data["effectifs"], marker="o", color="#55A868")
        ax.set_title("Évolution mensuelle des consultations")
        ax.set_xlabel("Mois")
        ax.set_ylabel("Nombre de consultations")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        return self._save(fig, "evolution_consultations.png")

    def repartition_hospitalisations(self) -> str:
        data = self.stats.duree_moyenne_hospitalisation_par_pathologie()
        fig, ax = plt.subplots(figsize=(8, 5))
        if data["pathologies"]:
            sns.barplot(x=data["duree_moyenne_jours"], y=data["pathologies"], ax=ax,
                        palette="magma", hue=data["pathologies"], legend=False)
        ax.set_title("Durée moyenne d'hospitalisation par pathologie")
        ax.set_xlabel("Durée moyenne (jours)")
        return self._save(fig, "repartition_hospitalisations.png")

    def generer_tous_les_graphiques(self) -> dict:
        return {
            "pyramide_ages": self.pyramide_des_ages(),
            "top_diagnostics": self.top_diagnostics(),
            "evolution_consultations": self.evolution_consultations(),
            "repartition_hospitalisations": self.repartition_hospitalisations(),
        }
