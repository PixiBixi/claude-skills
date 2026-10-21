# Schémas SVG (style maison)

Pour un diagramme d'architecture ou de flux, les skills `archify` et `artifact-diagramming` existent, mais le style maison ci-dessous prime pour les SVG du wiki. Dès que le schéma **encode des quantités** (barres, frise proportionnelle, courbe), c'est un graphique et pas un diagramme : invoquer le skill `dataviz` **avant** d'écrire le premier `<rect>` et faire tourner son validateur de palette, via le skill `dataviz` (lancer le script depuis le répertoire de ce skill, en dark puis en light).

Ce qu'il attrape et qu'on ne voit pas à l'œil : aplats trop saturés en gros blocs, absence de gap de 2px entre fills adjacents, libellés portant la couleur de la série au lieu d'une encre neutre et séparation insuffisante pour les daltonismes.

Un SVG du wiki doit passer le validateur **sur les 2 surfaces** : inliné il suit le thème, mais sa palette de fallback (RSS, sans JS) reste unique et doit tenir sur les 2 fonds. Éviter `fill-opacity` pour la même raison : le résultat dépend du fond, qu'on ne contrôle pas.

SVG écrits à la main, palette GitHub dark, `viewBox` ~640 de large, police Segoe UI. Boîtes = `rect` bordure `#30363d` + barre d'accent 4px colorée à gauche ; pills = `rect rx=12` bordure colorée.

Chaque teinte a **2 pas** : le vif pour les accents fins, l'atténué pour les aplats de données. Un aplat large en couleur vive tombe dans l'anti-pattern « thick saturated blocks », alors que la même couleur sur une barre d'accent de 4px est correcte.

| Rôle | Accent fin (barre 4px, stroke) | Aplat de données (barre, bande) |
|---|---|---|
| Succès / gate / spot | `#3fb950` | `#4e8f57` |
| Release / accent chaud | `#f78166` | `#c9714f` |
| Sécurité / info | `#58a6ff` | `#5b8fc9` |
| Neutre | `#8b949e` | `#8b949e` |

| Rôle | Couleur |
|---|---|
| Texte dans une boîte remplie | `#e6edf3` |
| Texte sur le fond de page | `#6e7781` + `font-weight="600"` |
| Texte secondaire / flèches / bordure | `#8b949e` / `#30363d` |
| Fond de boîte | `#161b22` |
| Fond (pour le rendu PNG uniquement) | `#0d1117` |

Marqueur flèche réutilisable :

```xml
<marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#8b949e"/>
</marker>
```

Toujours contrôler le rendu (`rsvg-convert` → PNG → Read) avant de committer : chevauchements de pills et largeurs de colonnes ne se voient pas dans le XML.

## Lisibilité dans les 2 thèmes

Un SVG en `<img>` ne voit ni les variables CSS de la page ni le toggle clair/sombre. `docs/javascripts/jd-svg.js` inline donc tout SVG dont la racine porte `data-jd-theme`, dans l'article **et** dans la lightbox glightbox (qui recrée sa propre `<img>` depuis le lien à l'ouverture), et suffixe ses ids. Un `@media (prefers-color-scheme)` dans le SVG suivrait l'OS et se désynchroniserait du toggle : ne pas l'utiliser.

Tout nouveau SVG est écrit thème-aware :

- racine `<svg class="jd-svg" data-jd-theme="" ... font-family="<pile Segoe UI>">` : l'attribut `font-family` est le fallback, une `var()` de police est invalide pour rsvg
- un `<style>` dont **chaque sélecteur est préfixé `.jd-svg `** (inliné, il fuit dans la page) et chaque couleur s'écrit `var(--jd-<token>, #<hex de la palette ci-dessus>)`. Aucun `fill="#..."` ni `stroke="#..."` en attribut, que des classes
- pas de `--` dans un commentaire XML (parse error), donc jamais de `var(--jd-...)` en commentaire
- référence : `docs/monitoring/lgtm/_img/thanos-flow.svg`

| Rôle | Token |
|---|---|
| Fond de boîte / fond plus profond | `--jd-surface-raised` / `--jd-surface` |
| Bordure de boîte | `--jd-border-strong` |
| Texte dans une boîte | `--jd-ink` |
| Texte secondaire, flèches, texte sur le fond de page | `--jd-muted` |
| Accent fin (barre 4px, stroke, texte coloré) | `--jd-{ok,warn,note,bad}-ink` |
| Aplat de données ou bande | `--jd-{ok,warn,note,bad}-border` |
| Aplat neutre **sous du texte** | `--jd-border-strong` |

Un aplat qui porte du texte ne prend jamais `--jd-muted` ni `--jd-accent` : tous 2 passent en teinte claire en sombre et le texte `--jd-ink` disparaît dessus (cas réels : la bande « pas de min-time » de thanos-sharding, 2 boîtes de ddos_decision_tree).

Les règles de lisibilité de la palette de fallback restent vraies, puisque c'est elle que voient le RSS et un navigateur sans JS :

- **texte dans une boîte** : donner un `fill` à la boîte, jamais `fill="none"`
- **texte posé sur le fond de page** : `#6e7781` + `font-weight="600"`, ni `#e6edf3` ni `#333`
- **ne pas** poser un grand `rect` sombre derrière tout le schéma

Contrôles, tous obligatoires :

```bash
# 1. le fallback ne bouge pas d'un pixel par rapport à la version committée
git show "HEAD:$F" > orig.svg
rsvg-convert -b '#fbfbf9' orig.svg -o orig.png && rsvg-convert -b '#fbfbf9' "$F" -o new.png
cmp orig.png new.png && echo IDENTICAL
xmllint --noout "$F"
# 2. aucun hex hors du <style>
rg -n '#[0-9a-fA-F]{3,6}\b' "$F"
```

3. Rendu réel sur `mkdocs serve -f mkdocs.dev.yml --livereload` (rebuild ~6s, voir l'`AGENTS.md` du repo), en clair **et** en sombre, avec Playwright (`channel: 'chrome'`, `colorScheme`, `waitUntil: 'load'` : livereload empêche `networkidle` de jamais se terminer). Capturer le schéma dans l'article **et la lightbox ouverte** : c'est là que le fond blanc est resté la première fois, et rien d'autre ne l'attrape.
