# Saclay Science Radar

Application statique française pour explorer les événements scientifiques, académiques et professionnels de Paris-Saclay et Paris. Profil : étudiant SupOptique, R&D photonique et matériel quantique expérimental.

## Fonctionnement

React 19, TypeScript strict et Vite. Données JSON collectées hors navigateur par Python 3.12 et GitHub Actions. Pas de serveur, de compte utilisateur, de base payante ni d’API d’IA. Favoris, préférences et annonces personnelles restent dans le navigateur.

- **Tout voir** : tous les scores, par ordre chronologique. Les événements passés sont accessibles en activant les archives ; aucun seuil de prix ou de score n’est implicite.
- **Pour moi** : même catalogue, tri par score explicable sur 100 (35 science, 20 networking, 15 géographie, 15 coût et accès, 10 métiers, 5 niveau).
- Recherche, période, dates, ville, zone, prix, discipline, organisateur, type, score, fiabilité, accès et format.
- Fiche, provenance, prix inconnu explicite, conseils distincts des faits, export ICS sans durée inventée, favoris et nouveautés depuis la précédente visite.
- Registre initial de 120 sources candidates. L’inventaire n’équivaut ni à 120 agendas validés, ni à 120 collecteurs opérationnels.
- Sources et couverture : résultats réels du pipeline, erreurs, dates de succès, URL finales, sources découvertes et limites.
- Ajout manuel local, export et import JSON. L’extraction d’une URL depuis le navigateur n’est pas implémentée : les données doivent être vérifiées dans l’annonce. Aucune donnée privée n’est publiée.

## Collecte et découverte

Connecteurs prédéfinis : JSON-LD `schema.org/Event`, calendriers ICS non récurrents, liens de flux RSS/Atom vers des pages d’événements, blocs HTML institutionnels, boutons calendrier Institut d’Optique/LCF, blocs d’agenda CEA IRAMIS. Les dates de publication RSS ne deviennent jamais des dates d’événement.

`collectors/source_discovery.py` découvre des liens d’agendas, d’annuaires et des flux sur les pages institutionnelles visitées. Un nouveau calendrier ICS du même domaine peut être activé après vérification robots, extraction et présence de dates valides. Les liens externes et formats nécessitant une intégration restent en file d’attente. Aucun moteur de recherche ni réseau social n’est faussement annoncé comme intégré. Pas d’exécution de code externe.

HTTP : identité explicite, robots.txt, requêtes espacées, limites de taille, délais, contrôle des IP publiques et des redirections, arrêt sur 429/503, aucun CAPTCHA contourné. Une erreur de source est isolée. En cas d’échec, les données connues sont conservées et vieillissent visiblement. Le respect de robots.txt ne remplace pas la vérification des conditions d’utilisation ; une source peut être désactivée dans le registre.

Le budget HTTP limite la charge **par exécution**, pas la taille du catalogue. Une file persistante conserve les pages de détail non encore visitées. La navigation profonde et les contenus JavaScript non structurés peuvent encore faire manquer des annonces. Les récurrences ICS RRULE sont signalées comme non prises en charge plutôt que mal interprétées. Une annonce sans date valide ne devient pas un événement confirmé.

Les sessions avec des horaires distincts ne sont pas fusionnées. La déduplication conservatrice maintient les provenances. Les modifications de date nécessitent un identifiant externe stable afin de limiter les fausses fusions. Les contradictions entre sources demandent encore une revue ; l’historique conserve les modifications reçues.

## Automatisation

Workflow `.github/workflows/radar.yml` :

- 06:15 UTC : collecte quotidienne de toutes les sources activées.
- 16:15 UTC : deuxième passage des sources prioritaires.
- Dimanche matin : découverte et contrôle d’URL candidates, dans le budget HTTP.
- Premier jour du mois : rapport de couverture et recalcul des audits indépendants disponibles.
- Exécution manuelle disponible et première collecte sur modification du code.
- Tests Python et TypeScript, validation des données, build, persistance du catalogue, d’un instantané précédent et des rapports datés, artefact de rapport, publication Pages.

Les horaires Actions sont indicatifs : GitHub peut retarder ou désactiver un workflow planifié (notamment après une période d’inactivité du dépôt public). Le site alerte après 48 h sans collecte de données réussie. Un workflow présent n’est pas une preuve d’exécution.

Les permissions sont limitées par tâche : écriture du contenu pour les instantanés, `pages: write` et `id-token: write` pour la publication. Les données des sources ne modifient jamais les scripts ni les workflows.

GitHub Pages doit utiliser **GitHub Actions** comme source de publication. Le workflow tente l’activation native ; selon les droits du jeton Actions, l’administrateur du dépôt peut devoir sélectionner cette option une fois. Aucun déploiement n’est déclaré réussi sans résultat d’exécution et contrôle du site.

## Couverture et audits

Le rapport `public/data/coverage.json` sépare : inventaire, extraction validée par source, succès technique, fraîcheur et rappel sur un échantillon indépendant. L’exhaustivité globale reste inconnue. **95 % est un objectif, jamais un résultat implicite.**

Protocole indépendant : choisir des sources officielles représentatives et une fenêtre temporelle ; relever toutes leurs annonces ; enregistrer titres, dates et URL ; comparer au catalogue ; conserver les manqués ; publier le rappel observé et sa portée. Le relevé ne doit pas être produit par le collecteur évalué.

Les relevés indépendants vivent dans `data/audits/*.json` et comprennent `sourceId`, `window`, `reviewedAt`, `method` et `expected` (liste d’objets `title`, `date`, `url`). Aucun échantillon fictif n’est livré en production. Le recalcul mensuel ne remplace pas la constitution d’un nouvel échantillon. L’interface affiche « Non mesuré » en l’absence d’audit.

## Développement et vérification

Ces commandes sont destinées aux mainteneurs ; l’utilisateur n’a rien à installer sur sa tablette.

```sh
npm install
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
npm test
python -m collectors.pipeline --discover --audit
python -m collectors.validate
npm run build
```

Le verrou npm est généré puis conservé par la première exécution Actions si l’environnement de création ne peut pas accéder au registre npm. Les versions directes sont fixées dans `package.json` et `requirements.txt`.

`data/sources.json` est le registre persistant ; `public/data/` contient les fichiers publiés. Les données synthétiques n’existent que dans `tests/`. Aucun événement de démonstration n’est chargé par l’application.

## Limites de la V1

L’inventaire contient des liens non vérifiés. La liste des sources opérationnelles dépend des résultats de collecte, et non de la configuration. Pas de collecte automatique LinkedIn, intranet, messagerie, affiche ni newsletter privée. Pas de scraping massif des plateformes. Pas de promesse de stage, de réseau ou d’accès : les conditions non extraites restent « Non précisé ». Les conseils sont déterministes et généraux, sans invention de personnes ou d’exposants.

Le système est conçu pour évoluer par ajout de connecteurs testés et par audit. Il ne prouve pas une couverture globale exhaustive. Les échecs et travaux restant à faire sont visibles dans Sources et Couverture.
