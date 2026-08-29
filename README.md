# NWSL Guessing Game

An NWSL companion to the WNBA guessing games. Static HTML pages backed by a
single generated data file.

## How it works

- `get_players.py` pulls every NWSL team roster from ESPN's public API and
  writes `players.js` (a `const allPlayers = [...]` array with goals, assists,
  appearances, position, headshot URL, and more).
- `.github/workflows/update.yml` reruns the script every day at 6 AM UTC and
  commits any changes to `players.js`.
- Each `.html` page loads `players.js` and renders a game or tool. No build
  step, no framework.

## Pages

- `index.html` — hub / landing page.
- `rosters.html` — pick two teams and compare their squads.

## Run the data script locally

```
pip install requests
python get_players.py
```

## Preview locally

```
python -m http.server
```

Then open http://localhost:8000.
