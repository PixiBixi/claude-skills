# Before showing a prototype

Each item below was a defect the user caught on a shown mockup. Checking them first saves a review round.

## Readability and look

- Body text at least 17px, contrast AA in both themes, code names legible in the display font.
- Lighthouse accessibility at 95 or more in both themes: it catches what a screenshot hides (an icon or logo link without an accessible name, skipped heading levels, unlabelled inputs).
- Not AI-looking: no generic three-card grids, glassmorphism, gradient text, purple-blue washes, emoji icons, marquees, empty voids in cards.
- Grid and flex children get `min-width: 0`: a nowrap chip row or badge otherwise widens its column past 375px.
- On a showcase or portfolio site, the hero fills the first screen (`min-height: 100svh`, content centred); a service site keeps its quick actions above the fold instead. With a full-screen hero, the next section never peeks in at load, where its scroll-triggered reveal has not fired yet and it shows as a half-hidden fragment.

## Screenshots

Run `${CLAUDE_SKILL_DIR}/scripts/screenshot.sh <url> <out-dir>`: it captures 375, 768, 1440 and 2560px in both themes and names each file after its width and theme. Name the theme of each capture when showing it.

Open every capture before showing or judging it: a blank, unstyled or error page is a failed capture, not a finding about the site.

What the script works around, for a manual capture:
- Headless Chrome's `--window-size` lays out at 500px minimum and crops: use Playwright's `--viewport-size` (an iframe wrapper breaks on `X-Frame-Options`).
- CDNs and WAFs serve a 403/404 page or drop the CSS for a `HeadlessChrome` user agent: send the regular Chrome one.
- A capture of a page that scrolled (deep link) comes out blank: check the scroll landing with a same-origin iframe that reads `scrollY` and the target's `getBoundingClientRect().top`, dumped with `--dump-dom`.

Also check: no horizontal scroll, readable line length on wide screens, touch targets at least 44px, no hover-only interaction, reduced motion. Headless screenshots freeze animations: check motion in a real browser, or say it was not checked instead of claiming it works.

## Performance, on every prototype

- Libraries load with `defer`, and the main script runs on `DOMContentLoaded`: a plain inline script runs before deferred libraries and silently falls back to no-motion.
- The one or two font weights above the fold are preloaded (`<link rel="preload" as="font" crossorigin>`), self-hosted, `font-display: swap`.
- The LCP image (hero, first visible photo) gets `fetchpriority="high"` and is never lazy: lazy-loading it delays the LCP.
- Other images have `width`, `height` and `loading="lazy"`, webp cropped to their display ratio and sized for 2x display, EXIF stripped.
- No permanent `will-change`: each one pins a GPU layer, even when nothing moves.
- Infinite loops (CSS keyframes, `setInterval`, `repeat: -1` tweens) pause offscreen and in hidden tabs: an IntersectionObserver per section toggles a class that sets `animation-play-state: paused`, and JS loops check it or pause their tween.
- No CSS `transition` on `transform` for an element GSAP tweens: it lags every frame. Hover offsets go on the individual `translate`, `rotate` and `scale` properties, which compose with GSAP.
