# Version améliorée — 28 octobre 2026

Site : https://izzki.github.io/Saclay-science-radar/

## Corrections effectives

- Thème, mots-clés, tri chronologique, période, ville et budget visibles sans ouvrir les filtres avancés.
- Événements terminés masqués au chargement ; archives explicitement sélectionnées et chaque carte marquée Terminé, En cours ou Déjà commencé sans fin connue.
- Prise en compte de l’heure réelle, de Paris, des fins ICS exclusives et de la recherche à plusieurs mots séparés par des virgules.
- Collecteur PSL réparé : chaque titre conserve son propre lien et ses propres dates. Les anciens rattachements erronés sont mis de côté avec leur motif.
- RRULE, RDATE, EXDATE et RECURRENCE-ID développés, y compris les déplacements de séances et le changement d’heure.
- Validation automatique des candidats de sources : 120 entrées testées dans une première campagne à budget limité, puis nouveau contrôle des agendas exploitables. Les liens exportant une seule annonce ne deviennent pas artificiellement des agendas supplémentaires.
- Extraction des tarifs publiés, conditions d’accès et inscriptions. Les tarifs non publiés restent inconnus ; la gratuité étudiante n’est pas attribuée à tout le monde.
- Analyse depuis une URL publique : reconnaissance du catalogue, demande GitHub préremplie pour les nouveaux liens et collecteur automatisé réservé au propriétaire. Une validation de la demande sur GitHub est nécessaire, sans jeton dans le navigateur.
- Import privé ICS dans le navigateur uniquement, sans transfert au dépôt, avec récurrences et réimport des séances modifiées. Aucun accès privé direct n’est prétendu.

## Données et validation locale

Registre : 312 entrées ; 17 sources avec extraction concluante au dernier contrôle ; 189 candidats découverts ; 135 URL contrôlées. Catalogue : 362 annonces réelles, dont les archives.

44 tests Python, 22 tests TypeScript et six parcours Android Chromium ont réussi localement. Le workflow effectue à nouveau les contrôles avant publication et vérifie ensuite le site public. Le résultat du déploiement le plus récent est consultable dans Actions.

Les nouveaux sous-agendas incluent Paris-Saclay, ses facultés de pharmacie et médecine, LMPS, CEA SPEC et d’autres agendas validés du quantique/deeptech. Le registre garde les sources inaccessibles ou nécessitant un parseur dédié ; il n’est pas présenté comme entièrement intégré.

La couverture globale demeure inconnue. Le relevé limité à huit annonces sur une page du LCF ne constitue pas un audit représentatif de tout Paris-Saclay.

Les récurrences infinies ont une fenêtre glissante de deux ans à venir ; les formats trop denses sont signalés pour contrôle. Les sources privées exigent une autorisation spécifique ou un fichier fourni par l’utilisateur. Aucune donnée manquante n’est remplacée par une invention.
