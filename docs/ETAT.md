# État vérifié au 28 octobre 2026

Site public : https://izzki.github.io/Saclay-science-radar/

Dépôt : https://github.com/izzki/Saclay-science-radar

## Résultats constatés

- 309 entrées au registre : 120 initiales et 189 candidats découverts automatiquement par exploration de liens et de flux. Les candidats ne sont pas tous des agendas validés.
- 122 URL ont réussi un contrôle HTTP respectant robots.txt.
- 11 sources activées ont réellement extrait des événements. D’autres sources activées restent en erreur ou sans extraction concluante.
- 339 annonces au catalogue, dont 78 à venir ou en cours au 28 octobre 2026. 35 annonces ont une fiabilité faible et un avertissement explicite. Aucun jeu de données de démonstration n’est chargé.
- Séminaires, soutenances, conférences, workshops, forums métiers, salons et visites sont représentés. Optique, photonique, quantique, nanosciences, instrumentation et mathématiques figurent parmi les thématiques.
- Le dernier téléchargement réel a fini le 28 octobre 2026 à 15:30 UTC. Les reconstructions suivantes ont réutilisé ce corpus réel et validé son traitement, sans prétendre effectuer une nouvelle collecte.
- 31 tests Python, 11 tests TypeScript et trois parcours Chromium au format Android : exploration/filtres/sources, favoris persistants/fiche/ICS et ajout manuel local. Le build TypeScript strict et Vite est vérifié par Actions.
- Après déploiement, un contrôle HTTP réel charge le HTML, les fichiers JavaScript/CSS et le JSON public ; il vérifie les identifiants uniques et la cohérence du rapport.

## Audit indépendant

Le relevé manuel via navigation de la première page de l’agenda LCF comprend huit annonces à venir au 28 octobre 2026. Les huit sont retrouvées dans le catalogue. Le résultat 8/8 ne mesure que cette page à cet instant : il ne prouve pas une couverture représentative de Paris-Saclay. L’exhaustivité globale demeure inconnue ; l’objectif 95 % n’est pas annoncé comme atteint.

## Automatisation configurée et observée

La collecte complète a été exécutée dans GitHub Actions, ainsi que la découverte de candidats, les tests, la construction, la persistance des données et la publication. Planification : collecte quotidienne à 06:15 UTC, sources prioritaires à 16:15 UTC, découverte le dimanche matin et recalcul mensuel des audits disponibles. Les premières échéances planifiées n’ont pas encore été observées lors de ce bilan : une exécution sur modification du code ne prouve pas le respect futur de la planification.

## Limites

Une grande partie du registre reste à intégrer ou à valider. La découverte utilise des liens institutionnels et des flux ; aucun moteur de recherche ni accès aux réseaux privés n’est configuré dans l’automatisation. Les récurrences ICS ne sont pas encore développées. L’ajout manuel se fait sur l’appareil, avec formulaire et import/export ; l’extraction distante d’une URL depuis ce formulaire n’est pas implémentée.

La collecte PSL est suspendue après détection de métadonnées globales non rattachées aux bonnes pages. Ses annonces héritées restent visibles avec fiabilité faible et avertissement. Les tarifs, conditions d’accès et liens d’inscription manquants restent inconnus. Le système ne garantit ni l’accès aux laboratoires ni une rencontre professionnelle.

Les exclusions de rubriques de navigation ou d’événements purement artistiques/festifs sans lien scientifique identifiable sont documentées dans `data/quarantine.json`. Aucun score ni prix n’entraîne une suppression. Les annonces incertaines restent accessibles dans le catalogue exhaustif.

L’activation initiale de GitHub Pages a nécessité la sélection « GitHub Actions » par le propriétaire du dépôt. Cette étape est terminée ; aucune intervention manuelle régulière n’est nécessaire pour exécuter les workflows configurés. Un audit indépendant nouveau et l’intégration de connecteurs spécifiques restent des travaux de maintenance.
