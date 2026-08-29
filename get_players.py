import json
import requests

LEAGUE = "usa.nwsl"
BASE = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE}"


def stat_value(player, category, name, default=0.0):
    """Pull a single numeric stat out of the roster-embedded statistics block."""
    splits = (player.get("statistics") or {}).get("splits") or {}
    for cat in splits.get("categories", []):
        if cat.get("name") != category:
            continue
        for s in cat.get("stats", []):
            if s.get("name") == name:
                try:
                    return float(s.get("value"))
                except (ValueError, TypeError):
                    return default
    return default


def fetch_nwsl_data():
    # Unlike the WNBA (basketball) API, the soccer "byathlete" statistics
    # endpoint returns nothing for NWSL. Instead, each team's roster response
    # embeds per-player season totals under player["statistics"], so a single
    # pass over the rosters gives us everything.
    teams_url = f"{BASE}/teams"
    print("Fetching NWSL teams and rosters...")
    response = requests.get(teams_url, timeout=20)
    response.raise_for_status()
    teams_data = response.json()

    players_list = []
    seen_ids = set()

    sports = teams_data.get("sports", [])
    leagues = sports[0].get("leagues", []) if sports else []
    teams_array = leagues[0].get("teams", []) if leagues else []

    for item in teams_array:
        team_obj = item.get("team", {})
        team_id = team_obj.get("id")
        team_name = team_obj.get("displayName", "Unknown Team")
        if not team_id:
            continue

        roster_url = f"{BASE}/teams/{team_id}/roster"
        try:
            r = requests.get(roster_url, timeout=15)
            if r.status_code != 200:
                print(f"Skipping {team_name}: roster HTTP {r.status_code}")
                continue
            roster_data = r.json()
        except Exception as e:
            print(f"Error fetching roster for {team_name}: {e}")
            continue

        athletes = roster_data.get("athletes", [])
        for entry in athletes:
            # NWSL roster entries are flat player objects; guard for the
            # grouped {"items": [...]} shape just in case ESPN changes it.
            player_items = entry.get("items", []) if "items" in entry else [entry]
            for player in player_items:
                pid = player.get("id")
                name = player.get("displayName") or player.get("fullName")
                if not pid or not name or pid in seen_ids:
                    continue
                seen_ids.add(pid)

                pos_obj = player.get("position") or {}
                position = pos_obj.get("abbreviation") or pos_obj.get("displayName", "Player")
                position_name = pos_obj.get("displayName", position)

                jersey = player.get("jersey") or player.get("uniformNumber") or ""
                birth_place = player.get("birthPlace") or {}
                status = player.get("status") or {}
                injuries = player.get("injuries") or []
                injury_status = next(
                    (inj.get("status") for inj in injuries if inj.get("status")), ""
                )
                profile_link = next(
                    (
                        link.get("href")
                        for link in player.get("links", [])
                        if "athlete" in link.get("rel", [])
                        and link.get("href", "").startswith("http")
                    ),
                    "",
                )

                goals = stat_value(player, "offensive", "totalGoals")
                assists = stat_value(player, "offensive", "goalAssists")

                players_list.append(
                    {
                        "id": pid,
                        "name": name,
                        "team": team_name,
                        "position": position,
                        "positionName": position_name,
                        "jersey": str(jersey),
                        "age": player.get("age"),
                        "height": player.get("displayHeight", ""),
                        "citizenship": player.get("citizenship", ""),
                        "birthPlace": ", ".join(
                            filter(
                                None,
                                [
                                    birth_place.get("city"),
                                    birth_place.get("state"),
                                    birth_place.get("country"),
                                ],
                            )
                        ),
                        "status": injury_status
                        or status.get("displayName")
                        or status.get("name", ""),
                        "profile": profile_link,
                        "goals": int(goals),
                        "assists": int(assists),
                        "goalContributions": int(goals + assists),
                        "appearances": int(stat_value(player, "general", "appearances")),
                        "shots": int(stat_value(player, "offensive", "totalShots")),
                        "shotsOnTarget": int(stat_value(player, "offensive", "shotsOnTarget")),
                        "yellowCards": int(stat_value(player, "general", "yellowCards")),
                        "redCards": int(stat_value(player, "general", "redCards")),
                        "saves": int(stat_value(player, "goalKeeping", "saves")),
                        "goalsConceded": int(stat_value(player, "goalKeeping", "goalsConceded")),
                        "headshot": f"https://a.espncdn.com/i/headshots/soccer/players/full/{pid}.png",
                    }
                )

    print(f"Successfully processed {len(players_list)} players across {len(teams_array)} teams.")
    return players_list


def save_to_js(players, filename="players.js"):
    players_sorted = sorted(
        players, key=lambda x: (x["goals"], x["goalContributions"]), reverse=True
    )
    file_content = f"const allPlayers = {json.dumps(players_sorted, indent=2)};\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(file_content)
    print(f"Saved player data to {filename}")


if __name__ == "__main__":
    try:
        players = fetch_nwsl_data()
        if players:
            save_to_js(players)
        else:
            print("Warning: No players returned.")
            exit(1)
    except Exception as e:
        print(f"Error fetching data: {e}")
        exit(1)
