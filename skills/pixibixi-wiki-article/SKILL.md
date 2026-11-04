---
name: pixibixi-wiki-article
description: >-
  Use when writing, updating, cross-linking or adding a diagram to an article on the PixiBixi wiki (pixibixi.github.io, wiki.jdelgado.fr): "écris un article wiki", "documente X sur le wiki", "ajoute une page", "rajoute un schéma". Not for fact-checking an article (wiki-fact-check).
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
| Build local (repro CI) | `DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$HOME/lib:/usr/local/lib:/usr/lib" uv run properdocs build --strict` (Gotcha 4) |
| Lint markdown (repro CI) | `npx -y markdownlint-cli2@0.23.0 --config .markdownlint.json <fichiers.md>` |
| Rendu SVG en PNG (contrôle visuel) | `rsvg-convert -b '#0d1117' fichier.svg -o out.png` |
| Nav | **auto-générée depuis l'arborescence** (pas de bloc `nav:` dans `properdocs.yml`) |

## Workflow

1. **Explorer** la section cible et **lire un article voisin** pour caler le style (frontmatter, ton, structure).
2. **Rédiger** l'article. Ancrer sur du réel (code, mesures, repos existants), pas du tuto générique. Une valeur par défaut, un chiffre de perf ou un nom de métrique s'écrit **avec sa source sous les yeux** : sinon on ne l'écrit pas, on va la chercher. Sur 9 articles relus, ces 2 familles pesaient 17 erreurs sur 49. Style (typographie, titres, ouverture, phrases) : `references/style.md`.
3. **Passer la voix au filtre** - invoquer le skill `humanizer` (obligatoire, pas optionnel) pour que ça sonne comme l'auteur, pas comme un bot. Tournures rejetées à chaque relecture : slogan à deux-points (`Notre compromis : ...`), phrase qui commence par `Encore`, `tout seul, parce que`, `voie médiane`, `, ce ...` en relance. Le hook `wordlist-guard` signale les plus fréquentes.
4. **Cross-linker** les articles liés (dans les deux sens) via une admonition `!!! tip` ou un lien inline.
5. **Schéma** si un *flux* le mérite (voir "Schémas SVG"). Sinon un tableau suffit.
6. **⚠️ Wirer les DEUX index** (voir Gotcha 1) - l'étape le plus souvent oubliée.
7. **Build + vérifier** : `properdocs build --strict` préfixé du `DYLD_FALLBACK_LIBRARY_PATH` (Gotcha 4), puis relint markdown (Gotchas 2, 3 et 5). Contrôler que le SVG est copié et la balise `<img>` résolue.
8. **Vérifier l'exactitude** - invoquer le skill `wiki-fact-check`. L'étape 7 prouve que l'article s'affiche, pas qu'il dit vrai. Sur un article neuf ou une réécriture de fond, c'est non négociable. Le rapport passe par l'auteur avant correction.
9. **Montrer le diff à l'auteur** après toute passe qui touche à la prose (wording, corrections du fact-check) : `python3 -I scripts/wiki_compare.py` depuis le repo (en arrière-plan, le serveur de dev doit tourner) ouvre la page live et la page locale côte à côte, scroll lié et blocs modifiés surlignés. On attend sa relecture avant de committer.
10. **Committer par scope** (Conventional Commits, un commit par portée), rebase sur `origin/master`, push.
11. **Watcher la CI**, seulement pour un article neuf ou sur demande : `gh run watch <id> --repo PixiBixi/pixibixi.github.io --exit-status`, fini quand `lint` **et** `deploy` sont verts. Petite mise à jour d'un article existant : lint + build strict en local (étape 7), push, donner le hash du commit, pas de watch.

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

## Style de rédaction

Lire `references/style.md` avant de rédiger (étape 2) : typographie et chiffres, titres (H1, H2, le gras n'est pas un titre), ouverture de l'article, construction de phrase. Les tournures qui sonnent faux sont dans `references/phrase.md` : le lire avant de rédiger et pendant la passe sur la voix (étape 3).

## Schémas SVG

Avant d'écrire ou de retoucher un SVG, lire `references/svg.md` : palette, SVG thème-aware (`data-jd-theme`, tokens `--jd-*`), contrôles obligatoires.

## Gotchas build et lint

Les 5 pièges (index à wirer, markdownlint sur les seuls fichiers changés, MD046 dans les admonitions, `DYLD_FALLBACK_LIBRARY_PATH`, ancres accentuées et MD051) sont détaillés dans `references/gotchas.md`. Le lire dès qu'un build ou un lint casse, et avant de poser un lien d'ancre.
