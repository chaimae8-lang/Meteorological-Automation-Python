import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


# ==================================================
# 1. CONFIGURATION
# ==================================================

VILLE = "Oujda"
LATITUDE = 34.6814
LONGITUDE = -1.9086

URL_API = "https://api.open-meteo.com/v1/forecast"

DOSSIER_SORTIE = Path(__file__).resolve().parent / "rapports_meteo"
DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

FICHIER_LOG = DOSSIER_SORTIE / "meteo.log"

# Configuration du journal : fichier + terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(FICHIER_LOG, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# ==================================================
# 2. RÉCUPÉRATION DES DONNÉES MÉTÉOROLOGIQUES
# ==================================================

def recuperer_donnees():
    logger.info("Début de la récupération des données pour %s", VILLE)

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "sunrise",
            "sunset",
        ],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
        ],
        "forecast_days": 7,
        "timezone": "Africa/Casablanca",
    }

    try:
        reponse = requests.get(
            URL_API,
            params=params,
            timeout=30,
        )
        reponse.raise_for_status()
        donnees = reponse.json()

        if "daily" not in donnees or "hourly" not in donnees:
            raise ValueError("La réponse de l'API est incomplète.")

        logger.info("Données météorologiques récupérées avec succès.")
        return donnees

    except (requests.RequestException, ValueError) as erreur:
        logger.exception("Erreur pendant la récupération : %s", erreur)
        raise


# ==================================================
# 3. TRAITEMENT DES DONNÉES
# ==================================================

def traiter_donnees(donnees):
    logger.info("Début du traitement des données.")

    quotidien = pd.DataFrame(donnees["daily"])
    horaire = pd.DataFrame(donnees["hourly"])

    if quotidien.empty or horaire.empty:
        raise ValueError("Les données météorologiques sont vides.")

    # Conversion des dates
    quotidien["time"] = pd.to_datetime(quotidien["time"])
    horaire["time"] = pd.to_datetime(horaire["time"])

    # Création d'une colonne date pour l'agrégation
    horaire["date"] = horaire["time"].dt.date
    quotidien["date"] = quotidien["time"].dt.date

    # Calcul des statistiques horaires par jour
    statistiques = horaire.groupby("date").agg(
        temperature_moyenne=("temperature_2m", "mean"),
        humidite_moyenne=("relative_humidity_2m", "mean"),
        precipitation_horaire_totale=("precipitation", "sum"),
        vent_moyen=("wind_speed_10m", "mean"),
    ).reset_index()

    # Fusion avec les prévisions journalières
    rapport = quotidien.merge(
        statistiques,
        on="date",
        how="left",
    )

    # Arrondi des colonnes numériques
    colonnes_numeriques = rapport.select_dtypes(
        include="number"
    ).columns

    rapport[colonnes_numeriques] = rapport[
        colonnes_numeriques
    ].round(2)

    logger.info("Traitement terminé : %d jours analysés.", len(rapport))

    return rapport, horaire


# ==================================================
# 4. GÉNÉRATION DES RAPPORTS
# ==================================================

def generer_rapport(rapport, horaire):
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")

    fichier_excel = DOSSIER_SORTIE / (
        f"rapport_meteo_{VILLE}_{horodatage}.xlsx"
    )
    fichier_csv = DOSSIER_SORTIE / (
        f"rapport_meteo_{VILLE}_{horodatage}.csv"
    )

    # Export CSV
    rapport.to_csv(
        fichier_csv,
        index=False,
        encoding="utf-8-sig",
    )
    logger.info("Fichier CSV généré : %s", fichier_csv)

    # Calcul du résumé
    resume = pd.DataFrame({
        "Indicateur": [
            "Ville",
            "Date de génération",
            "Température moyenne prévue (°C)",
            "Température maximale prévue (°C)",
            "Température minimale prévue (°C)",
            "Précipitations prévues cumulées (mm)",
            "Vitesse maximale du vent (km/h)",
        ],
        "Valeur": [
            VILLE,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            rapport["temperature_moyenne"].mean(),
            rapport["temperature_2m_max"].max(),
            rapport["temperature_2m_min"].min(),
            rapport["precipitation_sum"].sum(),
            rapport["wind_speed_10m_max"].max(),
        ],
    })

    # Arrondi des indicateurs numériques
    resume["Valeur"] = resume["Valeur"].apply(
        lambda valeur: (
            round(float(valeur), 2)
            if isinstance(valeur, (int, float))
            else valeur
        )
    )

    # Export Excel : trois feuilles
    with pd.ExcelWriter(
        fichier_excel,
        engine="openpyxl",
    ) as writer:
        resume.to_excel(
            writer,
            sheet_name="Résumé",
            index=False,
        )
        rapport.to_excel(
            writer,
            sheet_name="Prévisions journalières",
            index=False,
        )
        horaire.to_excel(
            writer,
            sheet_name="Données horaires",
            index=False,
        )

    logger.info("Fichier Excel généré : %s", fichier_excel)

    # Affichage du résumé dans le terminal
    print("\n" + "=" * 45)
    print("       RÉCAPITULATIF MÉTÉOROLOGIQUE")
    print("=" * 45)
    print(f"Ville : {VILLE}")
    print(
        "Température moyenne : "
        f"{rapport['temperature_moyenne'].mean():.1f} °C"
    )
    print(
        "Température maximale : "
        f"{rapport['temperature_2m_max'].max():.1f} °C"
    )
    print(
        "Température minimale : "
        f"{rapport['temperature_2m_min'].min():.1f} °C"
    )
    print(
        "Précipitations cumulées : "
        f"{rapport['precipitation_sum'].sum():.1f} mm"
    )
    print(
        "Vitesse maximale du vent : "
        f"{rapport['wind_speed_10m_max'].max():.1f} km/h"
    )
    print("=" * 45)
    print(f"Dossier des rapports : {DOSSIER_SORTIE}")
    print(f"Fichier journal : {FICHIER_LOG.resolve()}")

    logger.info("Génération de tous les rapports terminée.")


# ==================================================
# 5. FONCTION PRINCIPALE
# ==================================================

def main():
    logger.info("========== DÉMARRAGE DU PROGRAMME ==========")

    try:
        donnees = recuperer_donnees()
        rapport, horaire = traiter_donnees(donnees)
        generer_rapport(rapport, horaire)

        logger.info("Programme terminé avec succès.")

    except Exception:
        logger.exception("Échec de l'exécution du programme.")
        raise SystemExit(1)


# ==================================================
# 6. POINT D'ENTRÉE
# ==================================================

if __name__ == "__main__":
    main()