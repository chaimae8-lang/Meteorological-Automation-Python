# 🌦️ Meteorological Automation with Python

## 📝 Description
Ce projet consiste à automatiser la collecte, le traitement et la génération de rapports météorologiques à partir de l'**API Open-Meteo**. Il permet d'extraire des données climatiques précises, de les structurer sous forme de rapports exploitables et d'assurer un suivi rigoureux des exécutions grâce à un système de journalisation (logs).

## ✨ Fonctionnalités
* **Récupération automatisée** des prévisions météorologiques.
* **Collecte de données clés** : températures, humidité, précipitations et vitesse du vent.
* **Traitement et agrégation** fluide des données récoltées.
* **Génération automatique de rapports** exportés directement aux formats Excel (`.xlsx`) et CSV (`.csv`).
* **Création d'un fichier journal (`.log`)** pour le suivi des exécutions et l'historique des erreurs.
* **Gestion robuste des erreurs** liée aux pannes ou coupures de connexion à l'API.

## 🛠️ Technologies utilisées
* **Langage :** Python
* **Collecte de données :** Requests
* **Traitement de données :** Pandas
* **Génération Excel :** OpenPyXL
* **Journalisation :** Logging

## 🌐 API Utilisée
Ce projet s'appuie entièrement sur les services gratuits et open-source de la plateforme Open-Meteo.
* **Source :** Open-Meteo – Documentation officielle