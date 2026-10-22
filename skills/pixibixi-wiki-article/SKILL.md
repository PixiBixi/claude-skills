---
name: pixibixi-wiki-article
description: Use when writing, adding, updating, cross-linking, or adding a diagram to an article on the PixiBixi wiki (repo pixibixi.github.io, served at wiki.jdelgado.fr, MkDocs Material, docs/ tree). Triggers - "écris/ajoute un article wiki", "documente X sur le wiki", "ajoute une page", "rajoute un schéma à la page", "link entre deux articles du wiki".
---

# Écrire un article sur le wiki PixiBixi

## Overview

Le wiki est un site **MkDocs Material** (repo GitHub `PixiBixi/pixibixi.github.io`), déployé sur `wiki.jdelgado.fr` via GitHub Actions (`gh-deploy`) à chaque push sur `master`. Un article = un `.md` sous `docs/<section>/`. La prose est en **français**, le code/commits/technique en **anglais**.

Ce skill capture la procédure complète *et les pièges qui cassent la CI ou laissent l'article invisible*.

## Quick reference

| Élément | Valeur |
|---|---|
| Repo | `pixibixi.github.io` (branche `master`) |
| Articles | `docs/<section>/<nom>.md` (ex. `docs/ci-cd/github/go-ci.md`) |
| Build local (repro CI) | `DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$HOME/lib:/usr/local/lib:/usr/lib" uv run mkdocs build --strict` (Gotcha 4) |
| Lint markdown (repro CI) | `npx -y markdownlint-cli2@0.23.0 --config .markdownlint.json <fichiers.md>` |
| Rendu SVG en PNG (contrôle visuel) | `rsvg-convert -b '#0d1117' fichier.svg -o out.png` |
| Nav | **auto-générée depuis l'arborescence** (pas de bloc `nav:` dans `mkdocs.yml`) |

## Workflow

1. **Explorer** la section cible et **lire un article voisin** pour caler le style (frontmatter, ton, structure).
2. **Rédiger** l'article. Ancrer sur du réel (code, mesures, repos existants), pas du tuto générique. Une valeur par défaut, un chiffre de perf ou un nom de métrique s'écrit **avec sa source sous les yeux** : sinon on ne l'écrit pas, on va la chercher. Sur 9 articles relus, ces 2 familles pesaient 17 erreurs sur 49.
3. **Passer la voix au filtre** - invoquer le skill `humanizer` pour que ça sonne comme l'auteur, pas comme un bot.
4. **Cross-linker** les articles liés (dans les deux sens) via une admonition `!!! tip` ou un lien inline.
5. **Schéma** si un *flux* le mérite (voir "Schémas SVG"). Sinon un tableau suffit.
6. **⚠️ Wirer les DEUX index** (voir Gotcha 1) - l'étape le plus souvent oubliée.
7. **Build + vérifier** : `mkdocs build --strict` préfixé du `DYLD_FALLBACK_LIBRARY_PATH` (Gotcha 4), puis relint markdown (Gotchas 2, 3 et 5). Contrôler que le SVG est copié et la balise `<img>` résolue.
8. **Vérifier l'exactitude** - invoquer le skill `wiki-fact-check`. L'étape 7 prouve que l'article s'affiche, pas qu'il dit vrai. Sur un article neuf ou une réécriture de fond, c'est non négociable. Le rapport passe par l'auteur avant correction.
9. **Committer par scope** (Conventional Commits, un commit par portée), rebase sur `origin/master`, push.
10. **Watcher la CI** : `gh run watch <id> --repo PixiBixi/pixibixi.github.io --exit-status`. Ne pas considérer le travail fini avant que `lint` **et** `deploy` soient verts.

## Conventions MkDocs Material

- **Frontmatter** obligatoire : `description:` (une phrase riche en mots-clés, dont l'énumération se passe d'articles : « maxconn, buffers, sysctls et déploiement Kubernetes ») + `tags:` (liste).
- **Admonitions** : `!!! note`, `!!! warning`, `!!! tip "Titre"` (contenu indenté de 4 espaces).
- **Blocs de code titrés** : ` ```yaml title=".github/workflows/ci.yml" `.
- **Commande et sortie dans un seul bloc `console`**, la commande préfixée de `$ `. Un bloc `bash` suivi d'un bloc `text` pour la sortie se lit comme 2 extraits sans rapport.
- **Une liste dont chaque item porte un oui/non et sa raison devient un tableau** (`Opération | Couverte | Pourquoi`), comme 2 listes « ce qui passe » et « ce qui ne passe pas ».
- **Les outils de l'auteur** : quand l'article montre une commande manuelle qu'un de ses projets couvre déjà (klens pour l'inspection read-only d'un cluster, par exemple), proposer de la remplacer par l'outil, lien vers le repo compris. Ses sites de référence (rules.jdelgado.fr pour les règles Prometheus) vont aussi dans « Voir aussi », avec un lien direct sur le fichier concerné.
- **Un tableau et le bloc de code qui le suit gardent le même ordre** : si le tableau présente `low` puis `high`, la config et la prose qui suivent aussi, sinon le lecteur croit les sens inversés.
- **Liens internes** : chemins relatifs vers le `.md` (`goreleaser.md`, `github/go-ci.md`) - MkDocs les résout.
- **Images/SVG** : `![Alt](nom.svg)` avec le fichier dans le même dossier que l'article.

## Typographie et chiffres

Le `CLAUDE.md` du projet porte le style de fond (ton, structure, tournures). Ce qui suit complète sur des points qu'aucun lint n'attrape.

- **Jamais d'em dash (`U+2014`, tiret cadratin)**, nulle part : ni dans la prose, ni dans les titres, ni dans les descriptions de front matter, ni dans les commentaires d'un bloc de code. C'est la signature la plus visible d'un texte généré. À la place, un `-`, une virgule, ou on coupe la phrase en deux (pas un deux-points, voir « Construire une phrase »). Les incises appariées (mot, tiret cadratin, aparté, tiret cadratin, suite) passent en virgules ou en parenthèses, jamais en deux tirets : ça se lit mal et un `-` en début de ligne est parsé comme un item de liste par markdownlint.
- **Jamais d'en dash (`U+2013`, tiret demi-cadratin) non plus**, et il arrive surtout dans les plages : versions, nombres, dates. On écrit `HAProxy 2.4 à 3.2`, pas `2.4` et `3.2` reliés par un `U+2013`. Même raison que l'em dash, il ne se tape pas au clavier. Selon la phrase : `à`, `de X à Y`, ou un simple `-`.
- **Chiffres toujours en chiffres, jamais en lettres** : « 3 shards », « 12 fichiers », « 100 caches », y compris en début de phrase. Seule exception, les approximations restent en lettres (« une vingtaine de clusters », « la centaine de pods ») - les écrire en chiffres inventerait une précision qui n'existe pas.
- **Un chiffre précis se justifie sur place, sinon il n'y est pas.** Écrire « garde 14 mois de métriques » en intro alors que le 14 vient d'un palier expliqué 100 lignes plus loin laisse le lecteur devant un nombre arbitraire. Soit on explique là, soit on reste générique (« aussi longtemps qu'on le lui demande ») et le chiffre arrive avec sa raison.

    Un chiffre faux ou non sourcé ne se corrige pas en adverbe. Remplacer « 4-5x moins
    cher » par « nettement moins cher » efface l'erreur et l'information avec. Chercher
    le chiffre que l'éditeur publie, même partiel (« jusqu'à 91 % », doc Compute Engine),
    et le lier à sa source.
- **Unités de temps collées au chiffre** : `24h/24`, `12h`, `3h`, `6d`. Pas d'espace avant le symbole, c'est la convention de tout le wiki. La forme en mot (`12 heures`) reste valable en prose, mais on ne mélange pas `12 h` et `12h` dans le même article.
- **Guillemets français** `« … »` avec une espace intérieure, pas de `"…"` droits dans la prose. C'est la convention des articles récents.
- **Pas de virgule devant « et »**, ni devant « ou » et « ni ». C'est une faute, le réflexe vient de l'anglais où le comma before *and* est courant. On écrit « le cache et l'enveloppe mémoire », pas « le cache, et l'enveloppe mémoire ». Ça vaut aussi dans une énumération, où le français met la virgule entre les termes mais pas devant le dernier : « Ansible, Terraform et Makefile ». Attention au retour à la ligne, la faute se cache aussi à cheval sur 2 lignes, virgule en fin de ligne et `et` au début de la suivante, où un grep sur `, et` ne la voit pas.

    Une virgule qui **ferme une incise** juste avant le « et » est grammaticalement
    correcte (« le `main:` du build, qui vaut `""` tant qu'on ne l'a pas écrit, et ko
    passe cette chaîne vide »), mais l'auteur la refuse à la lecture comme les autres
    (« 3 caches, un par type de donnée, et ils… »). On ne la garde pas : on coupe la
    phrase ou on transforme l'incise en relative sans virgule. Un remplacement global ne
    la retire pas pour autant à l'aveugle, puisque retirer la seule virgule casse la phrase.
- **Genre des acronymes et des composants** : il suit le nom-tête de l'expression développée, pas l'anglais. Une TSDB (*Database*), une API (*interface*), une VM (*machine*), une stack (*pile*), une store gateway (*passerelle*), une query (*requête*). Mais **un querier**, qui est le composant et pas la requête, un query frontend dont la tête est *frontend*, un compactor. Accorder aussi les pronoms et adjectifs.

    L'accord voyage plus loin que le déterminant collé au mot, et c'est là que la faute
    survit à la relecture. `attend tous les stacks`, `partagés par tous les stacks` et
    `les stacks annotés` sont faux au même titre que `un stack`, mais un grep sur
    `un stack` n'en voit aucun. Chercher aussi les quantifieurs (`tous`, `certains`,
    `plusieurs`), les participes détachés du nom et les textes alternatifs des schémas,
    que personne ne relit.
- **Le vocabulaire du domaine, pas son équivalent français.** La règle n'est pas une liste de mots, c'est un critère : si le terme est celui qu'on lit dans les flags, les métriques, la doc amont ou les dashboards, il reste tel quel. Traduire oblige le lecteur à refaire la correspondance dans sa tête au moment où il cherche justement à retrouver un flag. `timerange` et pas « plage de temps » ni « tranche de temps », `replicas` et pas « réplicas », `at scale` et pas « à l'échelle », `évicté` et pas « évincé », pour le spot comme pour un cache, `rollback` et pas « revenir en arrière », `tuning` et `tuner` et pas « régler » quand on parle de l'acte d'optimiser (un « réglage » reste le mot pour une option précise), `lazy load` et `lazy download` et pas « lecture paresseuse » ni « téléchargement paresseux », même avec le flag sous les yeux. Les noms K8s et infra restent en anglais, sans accent.

    Ça vaut **surtout dans les titres et les textes alternatifs**, qui sont écrits en
    dernier et relus le moins : c'est là que la traduction survit, alors que le corps du
    texte emploie déjà le bon terme deux paragraphes plus haut. Avant de committer, grep
    les traductions des termes que l'article utilise vraiment, pas seulement celles listées
    ici, et vérifier le sommaire de droite qui n'affiche que les titres.

    L'inverse est vrai aussi, le critère n'est pas « angliciser par défaut ». Quand la
    phrase parle de l'acte et pas du composant, le mot français gagne : on écrit « la
    requête met 26 secondes » et pas « la query », alors que `query frontend` reste le nom
    du composant et ne se traduit jamais. Même partage entre `un cache` et le fait de
    cacher, `un shard` et le fait de découper.
- **Attention aux remplacements globaux** : `réplica` → `replica` mange aussi `réplication`, qui est un mot français et garde son accent. Ancrer les motifs sur une frontière de mot et relire le diff.

## Titres

### Le H1

Forme : `<Sujet> : <les axes couverts>`. On nomme les **axes**, pas les composants.

- ✅ `Thanos at scale : archi, perf et FinOps`
- ✅ `HAProxy performance tuning : nbthread, maxconn, TLS, Kubernetes`

Ce qui échoue :

- **lister des composants** quand l'article couvre toute la chaîne : `Thanos at scale : Receive, spot, compactor en CronJob` ne dit pas qu'on parle aussi d'archi et de coût
- **se décrire soi-même** - `nos arbitrages`, `nos apprentissages`, `retour d'expérience` sonnent robot
- **une redondance** - `at scale` porte déjà l'échelle, donc pas de `… sur une vingtaine de clusters` derrière
- **un seul angle** quand l'article en couvre trois - `ce que ça coûte vraiment` sous-vend un article qui parle aussi d'archi et de perf

### Les H2

2 formes, pas d'autre :

1. **infinitif + objet** - `Compacter sans payer le disque 24 h/24`, `Mettre des limites en lecture et en ingestion`, `Contenir la RAM de Receive`
2. **groupe nominal court**, éventuellement `Sujet : qualifier` - `Un shard par tranche de temps`, `Un seul cache chaud pour toute la flotte`, `Nos tests et nos échecs`, `Réplication : le choix assumé`, `Receive : le composant le plus cher`

Un titre à l'infinitif promet une action, donc il n'est valable que si la section fournit vraiment cette action. Quand elle ne fait que constater, c'est le groupe nominal qui va.

Un titre dit **ce que la section fait gagner**, pas le mécanisme qu'elle décrit :

| ✗ | ✅ | Pourquoi |
|---|---|---|
| `Le compactor en CronJob` | `Compacter sans payer le disque 24 h/24` | nomme le mécanisme, pas le gain |
| `L'arithmétique Hyperdisk, ou comment on paye un choix d'instances` | `Payer de la capacité disque pour acheter du débit` | tournure `X, ou comment Y` et vocabulaire vendeur dans le titre |
| `La query globale` | `L'architecture high-level` | titrait un composant alors que la section décrit l'archi |
| `Contenir la RAM de Receive` | `Receive : le composant le plus cher` | promet une action qu'on ne peut pas faire : la RAM suit la volumétrie, on agit sur ce qui la fait grossir, on ne la plafonne pas |

Le nom d'un produit vendeur (`Hyperdisk`, `Ketama`) reste dans le corps, pas dans le titre : il ferme le titre à ceux qui sont sur un autre cloud.

Un titre imagé ou elliptique (`Un block neuf est froid partout`) se refuse comme une phrase elliptique. Le titre dit la conséquence en clair : `Le cache ne survit pas à la compaction`. Quand l'auteur refuse un titre, proposer 3 options sous 3 angles (la limite, le symptôme, l'objet) avec une recommandation, plutôt qu'une seule retouche.

### Le gras n'est pas un titre

Un `**Label**` posé en tête de bloc pour annoncer ce qui suit est un titre déguisé. Il n'entre pas dans la nav, markdownlint ne le contrôle pas, et personne ne peut lier dessus. Il passe en `###`, et le deux-points de fin part avec lui.

- ✗ `**CPU** (progressif, toujours en millicores) :` suivi d'un bloc de code
- ✅ `### CPU (progressif, toujours en millicores)`
- ✗ `**Épingler la version.** Le cache local datait de plusieurs majeures...`
- ✅ `### Épingler la version` puis le paragraphe

Le gras reste légitime à l'intérieur d'une phrase, ou en tête d'item de liste : là il insiste, il n'annonce pas une section.

### Un projet tiers en titre porte son lien

Un titre qui nomme une librairie ou un outil tiers (`### Solution 1 - KimMachineGun/automemlimit`) pose le lien vers son repo sur le nom, dans le titre même : c'est là que le lecteur le cherche. Appliquer à tous les titres de l'article du même type, pas seulement à celui signalé.

## Construire une phrase

L'erreur la plus fréquente, c'est de découper pour faire du rythme. Une phrase longue construite en enchaînant des relatives passe très bien ; une suite de fragments courts sonne faux.

**Ne pas** viser un plafond de mots par phrase. Cette voix accepte 40 mots quand ils coulent :

> Une store gateway qui sert tout le bucket doit être dimensionnée pour la requête la plus
> violente qu'on lui posera jamais, par exemple un dashboard avec un timerange de 6 mois
> qui va charger énormément de donnée en RAM sur tous les replicas.

Ce qui sonne faux, à la place :

- **découper l'exemple en nouvelle phrase** avec une amorce du type « Concrètement : », « Résultat : », « Le point à retenir ». Enchaîner avec `, par exemple …` dans la même phrase.
- **les fragments d'insistance** posés après un point (« Même ceux qui… », « Et pas qu'un peu. »)
- **un deux-points suivi d'une énumération de trois** - figure qui annonce au lieu de dire
- **le verbe imagé** là où le mécanisme suffit : « force à gonfler la RAM » → « va charger énormément de donnée en RAM », « concentre le tir », « en tire 14 » → « concentre la charge », « en envoie 14 ». Une métaphore relevée revient souvent ailleurs dans l'article : la grep sous toutes ses formes (`tir`, `tire`, `tirés`).
- **le familier décoratif** (« on s'en fiche », « part en vrille », « à genoux »). Le blunt du `CLAUDE.md` est une réaction sincère, pas un ornement qu'on saupoudre.
- **le « X : Y » d'annonce** : « Notre compromis : … », « Le piège : son ordre », « Premier malentendu à lever. On… ». Une phrase complète, ou un point. « Le piège d'une liste dynamique, c'est son ordre. »
- **une phrase qui s'ouvre sur un connecteur ou un reste d'oral** : « Et », « Mais », « Or », « Encore faut-il », « Reste à », « Sauf que », « D'où », « Ça se lit… ». Reformuler avec un sujet (« Il faut ensuite choisir… », « Les métriques existantes le montraient déjà »). Même chose pour un paragraphe qui commence par du code inline : « Le flag `--x` … ».
- **les chaînes de conséquences** « , ce qui veut dire », « , donc … , donc », « , parce que », « tout seul, parce que ». Couper en 2 phrases. Une phrase longue passe quand ses relatives coulent, pas quand elle empile des conséquences ou 2 incises à virgules.
- **le raccourci elliptique** qui oblige à relire : « n'accuse pas son dashboard », « les plus lentes étaient triviales ». Dire le mécanisme en clair : « des requêtes simples qui attendaient la stack la plus lente ».
- **la règle avant sa raison** : « Cette liste doit sortir dans le même ordre » puis l'explication. Poser le problème d'abord, la règle ensuite.
- **un mot de remplacement pour un terme déjà posé** : « branche » ou « feuille » pour une stack, « nuance » pour ce qui décide de tout. Garder le mot de l'article.
- **un mot approximatif ou inventé pour un objet réel** : « le registre de clusters » pour le générateur `clusters` d'ArgoCD, « l'option qui rend le tout praticable ». Nommer l'objet tel qu'il existe.
- **un sujet vague** (« Le sujet a sa propre page », « le tout ») : nommer ce dont on parle, « Les caches sont un sujet à part entière ». Même chose pour un « On » plus pronom en tête de phrase (« On ne l'a pas mutualisé partout » devient « Chez nous, le cache n'est pas mutualisé sur toutes les stacks ») et pour un nom flou de remplissage (« ses voisins » pour les autres replicas, « unique globalement », « 2 montages » pour 2 topologies).
- **le verbe approximatif** : un serveur « implémente » un protocole et un port « sert » un protocole, ils ne le « parlent » pas.
- **la mini-phrase de conséquence** posée après un point (« pas par 6. Se tromper là sous-dimensionne d'un facteur 3. ») : la rattacher à la phrase qui la porte.
- **le détail qui ne sert pas la thèse** : une énumération de champs voisins (`metafile_exists_ttl`, `metafile_content_ttl`…) dans la phrase qui pose le piège de `blocks_iter_ttl`. On ne garde que celui qui compte, la phrase raccourcit d'elle-même.
- **une liste écrite en paragraphes** : des paragraphes qui commencent tous par « Le flag `--x` décide… » sont une liste, ils passent en puces sous une phrase d'intro terminée par « : ».
- **une option décrite sans dire laquelle on tourne** : après avoir présenté 2 stratégies ou 2 valeurs d'un flag, dire celle qu'on a (lue dans le repo, défaut compris) et pourquoi, en allant chercher la raison dans le code amont si elle n'a jamais été écrite (`recursive` passe par `IterWithAttributes`, que le caching bucket ne cache pas).
- **un lien sur le titre recopié** : poser le lien sur un groupe de mots court de la phrase, « ont [leur propre page](thanos-cache.md) ». Un renvoi à une section se fait en lien, pas en texte (voir `references/gotchas.md`, Gotcha 5).
- **le jargon non défini** (« fan-out ») : une infobulle dans `includes/abbreviations.md` plutôt qu'une définition en ligne. Les termes mis en regard reçoivent chacun la leur : ECDSA sans RSA laisse le titre « ECDSA ou RSA » à moitié expliqué.
- **« les défauts » employé seul** : on écrit « les valeurs par défaut » ou « les paramètres par défaut », « les défauts » se lit comme « les défaillances ».
- **le gras** : le réserver au mot qui porte la thèse (« **il attend** », « **le filtrage à la source** », « **amplificateur** »). Un gras orphelin dont le lecteur ne voit pas l'opposition (« que cette stack **annonce** ») s'écrit en clair.
- **l'absolu et le général non vérifiés** : « jamais », « irréductible pour tout le reste », « la moitié de ce qui la sollicite », « pousse la parallélisation plus haut » contredit 20 lignes plus bas. Chaque absolu se vérifie (code amont, config du repo) ou se nuance (« en principe », « certains déploiements »). Une recommandation ne se réécrit pas en « on a fait » sans preuve.
- **un comportement qui dépend de la version, sans date** : « avec RF=2 une éviction est survivable » n'est vrai que depuis Thanos v0.37. Dater le comportement, citer la PR, et passer en `!!! warning` si l'ancien comportement casse quelque chose. Un bug d'un outil tiers décrit au présent se recherche aussi en amont : les compteurs Dragonfly à zéro sont émis depuis la v2.0.0 (PR #8052) alors que la prod tourne en v1.37, donc on écrit « Avant la v2.0.0 » et la version qu'on fait tourner.
- **une cause affirmée puis démentie par l'article lui-même** : 2 sections accusaient `--query.max-concurrent-select`, puis les mesures montraient 1,5 sélecteur par requête et un cap sans effet. La cause annoncée en début d'article et la conclusion se relisent contre les mesures de la fin.
- **un histogramme nommé par sa famille** : `thanos_bucket_store_series_gate_queries_duration_seconds` ne renvoie rien dans un querier, seuls `_bucket`, `_sum` et `_count` portent des séries. Nommer la série que le lecteur va taper.
- **un correctif amont cru sur parole** : « corrigé en v0.35.0 » se vérifie dans le code, pas dans le titre de la PR. Le `ObjectStorageConfigHash` de Thanos hashe la config du caching bucket, pas celle du stockage objet, et ne cloisonne donc pas 2 buckets qui partagent un backend.
- **une limite ou un garde-fou recommandé sans ce qu'il casse** : une requête coupée par `--store.limits.*` n'est jamais servie et le dashboard échoue à chaque rafraîchissement. Chaque recommandation de ce type porte son encart `!!! warning`.
- **une description de notre infra recopiée de mémoire** : relire le repo actuel avant (l'ApplicationSet Thanos avait été réécrit depuis la rédaction).
- **une durée ou un chiffre propre à notre flotte présenté comme une loi** (« jusqu'à 30 minutes à redevenir prête ») : écrire la règle générique (« plus les index sont gros, plus la reprise est longue »), puis reprendre les renvois au chiffre ailleurs dans l'article.
- **le « je »**, et le « tu » ou le « vous » qui vont avec. Le wiki parle en « on », y compris pour un constat vécu : « Je n'ai pas trouvé de cas où… » devient « Aucun cas rencontré où… », « le mien datait de plusieurs majeures » devient « le cache local datait de plusieurs majeures ». On dépersonnalise sans effacer le constat.

## Schémas SVG

Avant d'écrire ou de retoucher un SVG, lire `references/svg.md` : palette, SVG thème-aware (`data-jd-theme`, tokens `--jd-*`), contrôles obligatoires.

## Gotchas build et lint

Les 5 pièges (index à wirer, markdownlint sur les seuls fichiers changés, MD046 dans les admonitions, `DYLD_FALLBACK_LIBRARY_PATH`, ancres accentuées et MD051) sont détaillés dans `references/gotchas.md`. Le lire dès qu'un build ou un lint casse, et avant de poser un lien d'ancre.

## Common mistakes

- Créer l'article et oublier de wirer `docs/index.md` **et** `docs/<section>/index.md` (Gotcha 1).
- Aligner/reformater des tableaux pour plaire à `MD060` - la règle est désactivée exprès (Gotcha 2).
- Mettre un bloc de code fencé dans une admonition, ou une admonition multi-paragraphes (Gotcha 3).
- Croire que l'échec `--strict` local vient de l'article, ou renoncer à `--strict` (Gotcha 4).
- Committer un gros commit fourre-tout au lieu d'un commit par scope.
- Écrire les chiffres en lettres (« trois shards ») au lieu de « 3 shards ».
- Titrer une section par son mécanisme (`Le compactor en CronJob`) au lieu de ce qu'elle fait gagner.
- Un H1 qui se décrit lui-même (`nos arbitrages`) ou qui ne couvre qu'un des axes de l'article.
- Découper un exemple en nouvelle phrase avec « Concrètement : » au lieu de `, par exemple …`.
- Viser un plafond de mots par phrase : ce n'est pas le critère, la construction l'est.
- Déclarer terminé sans avoir vu la CI verte (`lint` + `deploy`).
