# Saclay Science Radar

Veille scientifique et professionnelle pour un étudiant SupOptique à Paris-Saclay. Application française React/TypeScript/Vite, Python pour la collecte, GitHub Actions et GitHub Pages. Pas d’abonnement, d’IA payante, de serveur permanent ni de compte utilisateur sur le site.

**Site : https://izzki.github.io/Saclay-science-radar/**

## Explorer au quotidien

Les mots-clés, le thème, l’ordre de tri, la période, la ville et le budget sont directement visibles. Les thèmes rapides couvrent photonique, quantique, nanosciences, instrumentation, deeptech et physique ; le menu comprend toutes les disciplines du catalogue. La recherche couvre aussi les intervenants, organismes et entreprises. Plusieurs mots séparés par espaces ou virgules se combinent ; une expression entre guillemets est recherchée telle quelle.

Tri : dates croissantes, dates décroissantes, pertinence, dernières annonces et prix croissants avec inconnus à la fin. Les autres filtres précisent dates, zone, format, organisateur, type, fiabilité, score et conditions d’accès. La remise à zéro est accessible sans ouvrir les réglages avancés.

**Les événements terminés sont masqués par défaut, même si une ancienne préférence avait activé les archives.** Le menu « Période du catalogue » permet de consulter les archives. Les cartes et fiches distinguent Terminé, En cours, À venir, Aujourd’hui sans heure et Déjà commencé sans fin connue. La comparaison tient compte de l’heure réelle et de Paris ; la date de fin ICS exclusive est respectée. Une fin non publiée n’est pas inventée. Les événements annulés ou reportés ne proposent pas d’inscription active.

Favoris, préférences et annonces personnelles sont conservés localement. Les nouveautés dépendent de la dernière visite. L’export ICS respecte les fuseaux et les fins exclusives. La pondération des scores reste 35/20/15/15/10/5 ; aucun prix ou score ne supprime une annonce.

## Collecter et élargir les sources

Connecteurs fixes : JSON-LD Event rattaché au titre ou au lien de l’annonce, widgets institutionnels de calendrier, ICS, RSS/Atom vers pages datées et blocs HTML d’agendas. Une date de publication de news ne suffit pas à créer un événement.

Le collecteur PSL a été corrigé : titre, dates et lien sont lus **dans le même bloc d’événement**, sans choisir le lien d’un autre bloc. Les anciennes associations erronées sont conservées dans l’historique de qualité et remplacées par les annonces réextraites. Les tarifs, tarifs étudiants, conditions d’accès et liens d’inscription sont extraits lorsqu’ils sont explicitement publiés. Les contenus de navigation, newsletters et pieds de page ne servent pas de tarif à l’événement. Un tarif non publié reste inconnu ; un tarif étudiant gratuit ne signifie pas que l’entrée est gratuite pour tout public.

`source_discovery` découvre les liens publics de nouveaux agendas/flux ; `integration` teste les candidats existants avec les connecteurs validés. Jusqu’à quatre organismes sont contrôlés en parallèle, avec espacement global des requêtes par hôte. Le budget de requêtes limite chaque passage, **pas le catalogue**. Les candidats non encore visités et les échecs restent dans le registre ; les prochaines validations reprennent par les plus anciens tests. Les sources qui exigent un parseur spécifique ou refusent la collecte ne sont pas présentées comme surveillées.

Règles réseau : robots.txt, DNS public, rejet des adresses internes, redirections revérifiées, délais, limitation de taille et gestion 429/503. Pas de CAPTCHA contourné, de scraping privé ou d’exécution de scripts externes. L’ajout de connecteurs ne provient jamais d’un site distant.

## Calendriers récurrents

Le traitement Python utilise `recurring-ical-events` pour RRULE, RDATE, EXDATE et RECURRENCE-ID : séances exclues, déplacées, changements d’heure et annulations explicites. Les occurrences ont des identifiants distincts ; un changement horaire portant un identifiant stable conserve son historique.

Une série infinie ne peut pas être publiée sans borne : l’expansion porte sur les douze derniers mois et les deux prochaines années, et avance à chaque collecte. `RADAR_RECURRENCE_HORIZON_DAYS` configure l’horizon futur. Les règles à la seconde ou minute sont signalées pour contrôle plutôt que développées sans limite. Les événements simples passés restent archivés.

## Ajouter une URL publique

Le formulaire reconnaît immédiatement les URL déjà présentes. Pour une nouvelle page, le bouton ouvre une demande GitHub préremplie ; **le propriétaire doit valider cette demande sur GitHub**. Cette autorisation est nécessaire pour lancer un traitement sur un site statique sans serveur ni jeton dans le navigateur. Le workflow lit la page publique, teste ses dates, extrait et valide les informations, déduplique, calcule le score et republie le catalogue. Le formulaire affiche le résultat après publication via `data/imports.json`.

Seul le propriétaire du dépôt peut déclencher cet import. Le corps de la demande est lu comme des données JSON/texte, jamais comme du shell. Un lien contenant jeton, mot de passe ou signature n’est pas accepté dans ce circuit public. En cas d’échec ou d’annonce sans date exploitable, le résultat indique l’erreur et le formulaire manuel reste disponible : aucune date fictive ne remplace l’échec.

## Informations privées : sur l’appareil uniquement

Le formulaire accepte un fichier ICS exporté d’un calendrier autorisé, d’une invitation ou d’un intranet accessible par l’utilisateur. `ical.js` développe localement les récurrences et exceptions. Le fichier, ses descriptions et ses URL privées ne sont jamais envoyés au dépôt ou au collecteur. Un événement sans URL reste sans URL. Un réimport met à jour les séances portant le même identifiant et conserve l’historique local.

Cela ne donne pas un accès direct à un compte, un groupe privé, une messagerie ou un intranet. Une connexion automatique à ces services exige leur autorisation propre ; aucun accès n’est simulé et aucun identifiant n’est demandé dans le chat. Les sauvegardes JSON et ICS téléchargées restent sous le contrôle de l’utilisateur.

## Automatisation

- 06:15 UTC : collecte quotidienne de toutes les sources activées.
- 16:15 UTC : second passage des sources prioritaires.
- Dimanche matin : découverte et validation automatique des candidats dans le budget HTTP.
- Premier jour du mois : rapport de couverture et recalcul des échantillons indépendants disponibles.
- Demande d’import public par le propriétaire : traitement et publication de l’URL.
- Modification du code : réutilisation du corpus réel s’il date de moins de deux heures, sinon nouvelle collecte.

GitHub peut retarder/désactiver une planification : le site compare la dernière collecte réelle à l’heure actuelle et alerte après 48 h. Une reconstruction seule ne devient pas une nouvelle collecte. Instantané précédent, historique des événements, rapports datés par exécution et exclusions documentées sont persistés.

Les permissions sont définies par tâche : écriture du contenu pour les données, publication Pages et jeton d’identité pour le déploiement. Aucun secret utilisateur n’est nécessaire. Les tests et le build précèdent la publication ; le workflow vérifie ensuite l’URL publique, les assets et les données JSON.

## Couverture et fiabilité

Le tableau sépare inventaire, candidats découverts, URL contrôlées, sources ayant une extraction concluante au dernier passage, erreurs et fraîcheur. Une annonce incertaine reste signalée. Les exclusions de rubriques ou d’événements purement festifs sans lien scientifique sont conservées dans `data/quarantine.json` ; elles ne reposent pas sur le score.

Le relevé indépendant de la première page du LCF au 28 octobre 2026 compte huit annonces ; le rapport mesure celles retrouvées. Ce petit échantillon ne représente pas Paris-Saclay. **L’exhaustivité globale reste inconnue. 95 % est un objectif, pas un résultat.** Un nouveau relevé indépendant reste nécessaire pour étendre l’audit ; recalculer les résultats existants n’équivaut pas à constituer un nouvel échantillon.

## Vérification et maintenance

Commandes pour les mainteneurs uniquement ; rien à installer sur la tablette :

```sh
npm ci
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
npm test
npm run build
npm run test:browser
python -m collectors.pipeline --discover --integrate --audit
python -m collectors.validate
```

Les tests couvrent notamment échéances à l’heure réelle, archives, filtres et tris, tarifs inconnus/étudiants, déduplication et changements horaires, récurrences et exceptions, sécurité des demandes d’import, confidentialité locale et parcours Android. Les données synthétiques restent exclusivement dans les tests.
