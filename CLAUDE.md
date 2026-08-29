# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, no-build site of NWSL guessing games and tools. It is a soccer port of
a sibling WNBA project (`../wnba-guessing-game`); when adding a feature, check
whether the WNBA repo already has an equivalent page to adapt rather than
building from scratch. The maintainer is not a developer — when a task needs
action on GitHub (repo settings, Pages, Actions), give exact click-by-click
steps and do the local git/file work yourself.

## Commands

```bash
python get_players.py        # regenerate players.js from the live ESPN API
python -m http.server        # serve the site at http://localhost:8000
```

`get_players.py` needs `requests` (`pip install requests`). There is no test
suite, linter, or package manifest. Node is not installed — validate
`players.js` with Python, not `node -e`.

Sandboxed shells hit `SSLError` against `site.api.espn.com`; run
`get_players.py` with the sandbox disabled.

## Architecture

Three layers, connected only by a generated file:

1. **`get_players.py`** — walks every NWSL team roster from ESPN's public API
   (`site.api.espn.com/apis/site/v2/sports/soccer/usa.nwsl`) and writes
   **`players.js`**, a single `const allPlayers = [...]` sorted by goals
   descending. Key difference from the WNBA original: soccer's `byathlete`
   stats endpoint returns nothing, so per-player season totals are read out of
   the `statistics.splits.categories` block embedded in each roster response
   (`stat_value()` helper) — one pass over the rosters, no ID-matching step.
   Each player object carries `name`, `team`, `position` (GK/D/M/F),
   `goals`, `assists`, `goalContributions`, `appearances`, `saves`,
   `citizenship` (used where the WNBA version used `college`), and a
   `headshot` URL that is constructed unconditionally — NWSL headshot coverage
   is thin, so every `<img>` that uses it must have an `onerror` fallback.

2. **`players.js`** — the only data source. Committed to the repo and
   regenerated in place; treat it as a build artifact, not hand-edited.

3. **`*.html` pages** — one self-contained file per game/tool. Each is plain
   HTML/CSS/JS with no dependencies, loads `<script src="players.js?v=1">`,
   and reads the global `allPlayers`. `index.html` is the hub; `rosters.html`
   is the team-compare tool; `naming-challenge.html`, `crest-match.html`, and
   `stat-leaders.html` are the games. `crest-match.html` carries its own
   `teamCrests` map (team name → home city + ESPN team id) because crest images
   key off the numeric id at `a.espncdn.com/i/teamlogos/soccer/500/{id}.png`,
   not off `players.js`. `stat-leaders.html` quizzes the per-club leader in a
   rotating stat (goals, assists, goalContributions, saves, yellowCards);
   `appearances` is deliberately not a category because too many players tie at
   the season-game maximum. Ties for a lead are accepted — any option whose
   value equals the top value counts as correct.

### Daily refresh

`.github/workflows/update.yml` runs `get_players.py` on a 6 AM UTC cron and
commits `players.js` only if it changed. Hosting is GitHub Pages off `main` at
the repo root (`https://lacefaced.github.io/nwsl-guessing-game/`).

## Shared page conventions

Every HTML page copies the same design system inline — keep new pages
consistent with it rather than introducing a stylesheet:

- CSS custom properties on `:root` (`--ink`, `--paper`, `--coral`,
  `--coral-dark`, `--mint`, `--muted`, `--white`); Archivo Black / DM Mono /
  Manrope from Google Fonts; a fixed dotted-grid `body::before`; hard offset
  box-shadows.
- `⚽` SVG data-URI favicon.
- An `.hub-link` back to `index.html`; games also carry a `.game-nav` block
  linking the sibling pages, with the current page marked
  `class="active" aria-current="page"`.
- `naming-challenge.html`'s `normalizePlayerName` folds accents (NFKD +
  stripping `\p{Mn}`/`\p{Cf}`, plus explicit ø/ł/æ/ß), unifies apostrophes, and
  treats hyphens as spaces, so "Nadia" matches "Nádia Gomes". Its dropdown shows
  5+ character substrings anywhere in a name, plus any name part under 5
  characters once typed in full ("Sam", "Lara"). The "missed" list is ordered by
  appearances, then goal contributions.
- When a game is added, flip its `index.html` card from a disabled
  `<span class="game-card soon">` to an `<a class="game-card" href="...">` and
  add it to every page's `.game-nav`.
- The two-column game pages (`crest-match.html`, `stat-leaders.html`) share a
  `.board` grid that collapses to one column at `max-width: 700px`, with a
  second `max-width: 480px` block for phone-specific tightening (smaller `h1`,
  wrapped `.column-title`, shorter prompt/crest stage). Keep both breakpoints in
  sync across those pages. Note headless Chrome floors the viewport near 500px,
  so verify true phone width by loading the page inside a 375px `<iframe>`.
