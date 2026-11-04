## Typographie et chiffres

Le `CLAUDE.md` du projet porte le style de fond (ton, structure, tournures). Ce qui suit complète sur des points qu'aucun lint n'attrape.

- **Jamais d'em dash (`U+2014`, tiret cadratin)**, nulle part : ni dans la prose, ni dans les titres, ni dans les descriptions de front matter, ni dans les commentaires d'un bloc de code. C'est la signature la plus visible d'un texte généré. À la place, un `-`, une virgule, ou on coupe la phrase en deux (pas un deux-points, voir « Construire une phrase »). Les incises appariées (mot, tiret cadratin, aparté, tiret cadratin, suite) passent en virgules ou en parenthèses, jamais en deux tirets : ça se lit mal et un `-` en début de ligne est parsé comme un item de liste par markdownlint.
- **Jamais d'en dash (`U+2013`, tiret demi-cadratin) non plus**, et il arrive surtout dans les plages : versions, nombres, dates. On écrit `HAProxy 2.4 à 3.2`, pas `2.4` et `3.2` reliés par un `U+2013`. Même raison que l'em dash, il ne se tape pas au clavier. Selon la phrase : `à`, `de X à Y`, ou un simple `-`.
- **Chiffres toujours en chiffres, jamais en lettres** : « 3 shards », « 12 fichiers », « 100 caches », y compris en début de phrase. Seule exception, les approximations restent en lettres (« une vingtaine de clusters », « la centaine de pods ») - les écrire en chiffres inventerait une précision qui n'existe pas.
- **Un chiffre précis se justifie sur place, sinon il n'y est pas.** Écrire « garde 14 mois de métriques » en intro alors que le 14 vient d'un palier expliqué 100 lignes plus loin laisse le lecteur devant un nombre arbitraire. Soit on explique là, soit on reste générique (« aussi longtemps qu'on le lui demande ») et le chiffre arrive avec sa raison.

    Une mesure ponctuelle tirée d'un incident (« un job de 10 secondes qui en passe 76 en `Pending` ») ne se répète pas ailleurs : sa précision n'apprend rien au lecteur et date l'article. On garde l'ordre de grandeur (« plusieurs dizaines de secondes »), puis on reprend chaque renvoi au même chiffre dans l'article.

    Un chiffre faux ou non sourcé ne se corrige pas en adverbe. Remplacer « 4-5x moins cher » par « nettement moins cher » efface l'erreur et l'information avec. Chercher le chiffre que l'éditeur publie, même partiel (« jusqu'à 91 % », doc Compute Engine), et le lier à sa source.
- **Unités de temps collées au chiffre** : `24h/24`, `12h`, `3h`, `6d`. Pas d'espace avant le symbole, c'est la convention de tout le wiki. La forme en mot (`12 heures`) reste valable en prose, mais on ne mélange pas `12 h` et `12h` dans le même article.
- **Guillemets français** `« … »` avec une espace intérieure, pas de `"…"` droits dans la prose. C'est la convention des articles récents.
- **Pas de virgule devant « et »**, ni devant « ou » et « ni ». C'est une faute, le réflexe vient de l'anglais où le comma before *and* est courant. On écrit « le cache et l'enveloppe mémoire », pas « le cache, et l'enveloppe mémoire ». Ça vaut aussi dans une énumération, où le français met la virgule entre les termes mais pas devant le dernier : « Ansible, Terraform et Makefile ». Ça vaut encore quand le « et » relie 2 propositions qui ont chacune leur sujet (« n'est la CVE de personne, et govulncheck n'a rien à en dire »). C'est le cas qui survit le plus souvent à une passe wording : 7 des 9 restes de go-ci étaient de ce type. Si la phrase a besoin d'une pause, on la coupe ou on prend « mais » quand le sens s'oppose. Attention au retour à la ligne, la faute se cache aussi à cheval sur 2 lignes, virgule en fin de ligne et `et` au début de la suivante, où un grep sur `, et` ne la voit pas.

    Une virgule qui **ferme une incise** juste avant le « et » est grammaticalement correcte (« le `main:` du build, qui vaut `""` tant qu'on ne l'a pas écrit, et ko passe cette chaîne vide »), mais l'auteur la refuse à la lecture comme les autres (« 3 caches, un par type de donnée, et ils… »). On ne la garde pas : on coupe la phrase ou on transforme l'incise en relative sans virgule. Un remplacement global ne la retire pas pour autant à l'aveugle, puisque retirer la seule virgule casse la phrase.
- **Genre des acronymes et des composants** : il suit le nom-tête de l'expression développée, pas l'anglais. Une TSDB (*Database*), une API (*interface*), une VM (*machine*), une stack (*pile*), une store gateway (*passerelle*), une query (*requête*). Mais **un querier**, qui est le composant et pas la requête, un query frontend dont la tête est *frontend*, un compactor. Un nom de fichier prend le genre de *fichier* : un `renovate.json`, un `Dockerfile`. Accorder aussi les pronoms et adjectifs.

    L'accord voyage plus loin que le déterminant collé au mot, et c'est là que la faute survit à la relecture. `attend tous les stacks`, `partagés par tous les stacks` et `les stacks annotés` sont faux au même titre que `un stack`, mais un grep sur `un stack` n'en voit aucun. Chercher aussi les quantifieurs (`tous`, `certains`, `plusieurs`), les participes détachés du nom et les textes alternatifs des schémas, que personne ne relit.
- **Le vocabulaire du domaine, pas son équivalent français.** La règle n'est pas une liste de mots, c'est un critère : si le terme est celui qu'on lit dans les flags, les métriques, la doc amont ou les dashboards, il reste tel quel. Traduire oblige le lecteur à refaire la correspondance dans sa tête au moment où il cherche justement à retrouver un flag. `timerange` et pas « plage de temps » ni « tranche de temps », `replicas` et pas « réplicas », `at scale` et pas « à l'échelle », `évicté` et pas « évincé », pour le spot comme pour un cache, `rollback` et pas « revenir en arrière », `tuning` et `tuner` et pas « régler » quand on parle de l'acte d'optimiser (un « réglage » reste le mot pour une option précise), `lazy load` et `lazy download` et pas « lecture paresseuse » ni « téléchargement paresseux », même avec le flag sous les yeux. Les noms K8s et infra restent en anglais, sans accent.

    Ça vaut **surtout dans les titres et les textes alternatifs**, qui sont écrits en dernier et relus le moins : c'est là que la traduction survit, alors que le corps du texte emploie déjà le bon terme deux paragraphes plus haut. Avant de committer, grep les traductions des termes que l'article utilise vraiment, pas seulement celles listées ici, et vérifier le sommaire de droite qui n'affiche que les titres.

    L'inverse est vrai aussi, le critère n'est pas « angliciser par défaut ». Quand la phrase parle de l'acte et pas du composant, le mot français gagne : on écrit « la requête met 26 secondes » et pas « la query », alors que `query frontend` reste le nom du composant et ne se traduit jamais. Même partage entre `un cache` et le fait de cacher, `un shard` et le fait de découper.
- **Jamais de hard-wrap dans la prose** : un paragraphe tient sur une seule ligne, MkDocs et l'éditeur font le retour. Une coupe manuelle à 80 colonnes laisse des lignes inégales à chaque retouche, produit des diffs illisibles et cache les fautes à cheval sur 2 lignes. Un article reçu coupé se déplie avant toute relecture.
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

Un titre ne contredit pas sa section. `Absorber le cold start d'un node Spot` au-dessus d'une phrase qui explique que le cold start n'est pas propre à Spot fait relire le titre deux fois. Quand la section élargit le sujet, le titre suit : `Absorber le cold start du scale from zero`. Relire chaque titre contre la première et la dernière phrase de sa section.

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

## Ouvrir l'article

Le premier paragraphe ne commence pas par l'outil (« GoReleaser génère le changelog… ») : sous le H1, c'est trop brut. Il pose d'abord le problème que l'article résout, puis ce qu'on obtient à la fin, et l'outil n'arrive qu'après :

> Une release Go publiée à la main demande de compiler pour chaque plateforme, d'empaqueter, de calculer les checksums, de signer et d'écrire les notes. Chacune de ces étapes peut être oubliée sans que rien ne le signale. Le pipeline décrit ici les enchaîne toutes à partir d'un simple push sur `main` et publie les binaires multi-arch, l'image OCI, la signature, le SBOM et les notes de release.

Le paragraphe suivant ne répète pas ce que l'accroche a déjà énuméré. Quand l'auteur refuse une ouverture, proposer 3 accroches (le problème, le résultat, l'enjeu), il en combine souvent 2.

## Construire une phrase

L'erreur la plus fréquente, c'est de découper pour faire du rythme. Une phrase longue construite en enchaînant des relatives passe très bien ; une suite de fragments courts sonne faux.

**Ne pas** viser un plafond de mots par phrase. Cette voix accepte 40 mots quand ils coulent :

> Une store gateway qui sert tout le bucket doit être dimensionnée pour la requête la plus violente qu'on lui posera jamais, par exemple un dashboard avec un timerange de 6 mois qui va charger énormément de donnée en RAM sur tous les replicas.

### Un paragraphe, une idée

Le même travers existe à l'échelle du paragraphe. Un bloc de 8 phrases qui enchaîne ce que fait l'outil, sa version, ce qu'il hérite et ses limites fatigue l'œil. L'excès inverse sonne aussi faux : une phrase par paragraphe, avec une ligne vide entre chacune, découpe le raisonnement en slides (« Le second levier réserve de la capacité d'avance. » isolée, puis la version isolée, puis l'héritage isolé). On coupe là où l'idée change, ce qui donne en général des paragraphes de 2 à 4 phrases : ce que c'est et depuis quand, puis ce que ça reprend et comment on le règle, puis les limites.

Les tournures qui sonnent faux (amorces « Concrètement : », fragments d'insistance, chaînes de conséquences, absolus non vérifiés, « je »…) sont listées dans `references/phrase.md`. Le lire avant de rédiger (étape 2) et pendant la passe sur la voix (étape 3).
