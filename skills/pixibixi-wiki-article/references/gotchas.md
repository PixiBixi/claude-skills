# Gotchas build et lint

## Gotcha 1 - la nav auto NE référence PAS l'article dans les index

La nav latérale est auto-générée depuis l'arborescence, **mais il y a deux index maintenus à la main** qu'il faut éditer, sinon l'article est "orphelin" :

- `docs/index.md` - page d'accueil, section `## CI/CD` (ou la section concernée).
- `docs/<section>/index.md` - index de la section (ex. `docs/ci-cd/index.md`).

Après avoir créé l'article, **grep les deux** pour un article voisin et ajouter la ligne au même endroit :

```bash
rg -n 'goreleaser|cocogitto' docs/index.md docs/ci-cd/index.md
```

## Gotcha 2 - markdownlint ne lint QUE les fichiers changés

La CI `lint` passe les fichiers **modifiés dans le push** à `markdownlint-cli2`. Conséquence :

- Toucher un vieil article peut réveiller une règle récente sur ses tableaux et casser la CI sans rapport avec ton changement.
- **Politique du wiki** : tableaux compacts (`|---|`, sans alignement). `MD013` (longueur) et `MD060` (`table-column-style`) sont **désactivés** dans `.markdownlint.json` - ne pas les réactiver.

Toujours relinter en local **avant de pousser**, avec la version exacte de la CI :

```bash
npx -y markdownlint-cli2@0.23.0 --config .markdownlint.json docs/**/tes-fichiers.md
```

## Gotcha 3 - MD046 casse sur les admonitions

`markdownlint` ne connaît pas la syntaxe des admonitions MkDocs. Il lit le contenu indenté de 4 espaces comme un bloc de code indenté et `MD046` (`code-block-style: consistent`) casse. Deux cas :

- **un bloc de code fencé dans une admonition** → erreur systématique
- **une admonition à plusieurs paragraphes** → le 1er passe en continuation lâche, les suivants sont vus comme du code indenté

La bonne réponse est de **sortir le bloc de code de l'admonition** et de garder l'admonition à un seul paragraphe. Pas d'ajout de `<!-- markdownlint-disable MD046 -->` : plusieurs vieux articles en contiennent un jamais réactivé, ce qui désactive la règle sur toute la fin du fichier et masque de vraies erreurs.

Un repli `???` autour d'un bloc de code ne sert plus à rien non plus : `jd-codefold.js` replie tout bloc de plus de 30 lignes sur le site. Le titre de l'admonition devient le `title="..."` du bloc fencé. Le `???` reste réservé à de la prose qu'on cache exprès, comme une section archivée.

Les onglets (`=== "Label"`, `pymdownx.tabbed`) suivent la même mécanique. On colle le contenu indenté **directement** sous la ligne `=== "Label"`, sans ligne vide, et on ne met pas de ligne vide entre une phrase et un bloc fencé dans le même onglet : la ligne vide fait lire la suite comme du code indenté et MD046 casse. Le thème habille un onglet comme un bloc de code, donc on n'y met que du code ou une capture, et la phrase qui introduit les variantes reste au-dessus du groupe. Un onglet n'est valable que si le lecteur choisit une variante parmi plusieurs (distro, méthode d'install, shell, captures de dashboards), jamais pour des étapes à enchaîner. Les H3 remplacés par des onglets sortent du sommaire et perdent leur ancre.

## Gotcha 4 - `mkdocs build --strict` a besoin de `DYLD_FALLBACK_LIBRARY_PATH`

Le plugin `social` génère les cartes via `cairosvg`, qui charge `libcairo` par `dlopen`. Le Python de `uv` ne regarde pas dans Homebrew, d'où 244 warnings `cairo` (un par page) qui font abort `--strict` sans aucun rapport avec le contenu.

`~/.zshrc` exporte déjà la variable qui corrige ça, mais zsh ne source `.zshrc` que dans un shell **interactif** : un shell d'agent ne l'a jamais. Donc on préfixe la commande et on garde `--strict`, qui est exactement ce que fait la CI :

```bash
DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$HOME/lib:/usr/local/lib:/usr/lib" \
  uv run mkdocs build --strict
```

Avec ça le build sort en 0. Le seul warning non bloquant qui reste est `WARNING:root:` du plugin git-revision-date, y compris en `--strict`.

## Gotcha 5 - une ancre vers un titre accentué casse MD051

MkDocs et markdownlint ne calculent pas la même ancre. MkDocs retire les accents et la ponctuation (`## Payer de la capacité disque` donne `#payer-de-la-capacite-disque`), markdownlint garde les accents et transforme ` : ` en `--`. Un lien `[...](#ancre)` vers un titre qui porte un accent ou un deux-points ne peut donc satisfaire que l'un des 2 : le build passe et `MD051/link-fragments` casse la CI. L'auteur veut un vrai lien, pas un renvoi en texte. Quand une section doit être liée, la renommer pour que son ancre n'ait ni accent ni deux-points (`## Lazy load : le prix du rechargement` est devenu `## Le prix du rechargement en lazy load`), puis lier `#le-prix-du-rechargement-en-lazy-load` et relinter. Un id custom `{ #id }` via `attr_list` ne passe pas MD051. Le renvoi en texte reste le dernier recours, quand le titre ne peut pas changer (accent dans un mot indispensable), et après un renommage, grep `docs/` pour les liens vers l'ancienne ancre.
