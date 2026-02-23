"""
ESPN NBA Data Scraper — Enhanced Edition
========================================
Uses ESPN's public API endpoints (no API key required)

Modules:
  - Scoreboard / Schedule
  - Standings (full conference + division breakdown)
  - Teams & Rosters
  - Player Data (profile, season stats, game log, splits)
  - Advanced Team Analytics
  - Injury Reports
  - News
  - Game Summary / Box Score

Usage:
  python espn_nba_scraper.py                  # runs full demo
  from espn_nba_scraper import *              # import individual functions
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
CORE_URL = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba"
WEB_URL  = "https://site.web.api.espn.com/apis/v2/sports/basketball/nba"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def get(url: str, params: dict = None) -> Optional[dict]:
    """Generic GET with error handling. Returns parsed JSON or None."""
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] {url}\n         {e}")
        return None


# ═══════════════════════════════════════════════
# SECTION 1 — SCOREBOARD & SCHEDULE
# ═══════════════════════════════════════════════

def get_scoreboard(date: str = None) -> list:
    """
    Fetch NBA scoreboard for a given date (or today).

    Args:
        date: 'YYYYMMDD' string, e.g. '20260221'. Defaults to today.

    Returns:
        List of game dicts with scores, status, venue, odds, and leaders.
    """
    params = {"dates": date} if date else {}
    data = get(f"{BASE_URL}/scoreboard", params)
    if not data:
        return []

    games = []
    for event in data.get("events", []):
        comp = event["competitions"][0]
        home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
        away = next(c for c in comp["competitors"] if c["homeAway"] == "away")

        odds_raw = comp.get("odds", [{}])
        odds = odds_raw[0] if odds_raw else {}

        leaders = {}
        for side in [home, away]:
            abbr = side["team"]["abbreviation"]
            side_leaders = []
            for leader_group in side.get("leaders", []):
                for leader in leader_group.get("leaders", []):
                    side_leaders.append({
                        "category": leader_group.get("displayName"),
                        "player":   leader.get("athlete", {}).get("displayName"),
                        "value":    leader.get("displayValue"),
                    })
            leaders[abbr] = side_leaders

        games.append({
            "id":          event["id"],
            "name":        event.get("name"),
            "date":        event["date"],
            "status":      event["status"]["type"]["description"],
            "clock":       event["status"].get("displayClock", ""),
            "period":      event["status"].get("period", 0),
            "home_team":   home["team"]["displayName"],
            "home_abbr":   home["team"]["abbreviation"],
            "home_score":  home.get("score", "—"),
            "home_record": home.get("record", [{}])[0].get("summary", "") if home.get("record") else "",
            "away_team":   away["team"]["displayName"],
            "away_abbr":   away["team"]["abbreviation"],
            "away_score":  away.get("score", "—"),
            "away_record": away.get("record", [{}])[0].get("summary", "") if away.get("record") else "",
            "venue":       comp.get("venue", {}).get("fullName", "Unknown"),
            "city":        comp.get("venue", {}).get("address", {}).get("city", ""),
            "broadcast":   ", ".join(
                name for b in comp.get("broadcasts", [])
                for name in (b.get("names", []) if isinstance(b.get("names"), list) else [b.get("names", "")])
                if name
            ) if comp.get("broadcasts") else "",
            "spread":      odds.get("details", ""),
            "over_under":  odds.get("overUnder", ""),
            "leaders":     leaders,
        })
    return games


def get_schedule(team_abbr: str = None, limit: int = 20) -> list:
    """
    Fetch upcoming/recent NBA schedule.

    Args:
        team_abbr: Optional 3-letter abbreviation to filter (e.g. 'LAL').
        limit: Max number of games to return.

    Returns:
        List of game dicts.
    """
    params = {"limit": limit}
    if team_abbr:
        params["team"] = team_abbr
    data = get(f"{BASE_URL}/schedule", params)
    if not data:
        return []

    events = data.get("events", [])
    schedule = []
    for event in events[:limit]:
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        schedule.append({
            "id":     event.get("id"),
            "date":   event.get("date"),
            "home":   home.get("team", {}).get("displayName", "?"),
            "away":   away.get("team", {}).get("displayName", "?"),
            "status": event.get("status", {}).get("type", {}).get("description", "?"),
            "venue":  comp.get("venue", {}).get("fullName", ""),
        })
    return schedule


# ═══════════════════════════════════════════════
# SECTION 2 — STANDINGS (Enhanced)
# ═══════════════════════════════════════════════

def get_standings(season: int = None) -> dict:
    """
    Fetch full NBA standings with conference, division, and key stats.

    Args:
        season: Season year (e.g. 2026). Defaults to current season.

    Returns:
        Dict with 'East' and 'West' lists, each entry containing team name,
        W, L, PCT, GB, home/away splits, streak, last 10, and more.
    """
    params = {}
    if season:
        params["season"] = season

    data = get(f"{BASE_URL}/standings", params)
    if not data:
        return {}

    standings = {"East": [], "West": []}

    for child in data.get("children", []):
        conf_name = child.get("name", "")
        key = "East" if "East" in conf_name else "West"
        division_groups = child.get("children", [child])
        for div_group in division_groups:
            div_name = div_group.get("name", conf_name)
            for entry in div_group.get("standings", {}).get("entries", []):
                team_info = entry.get("team", {})
                stats = {s["name"]: s["displayValue"] for s in entry.get("stats", [])}
                standings[key].append({
                    "team":      team_info.get("displayName"),
                    "abbr":      team_info.get("abbreviation"),
                    "division":  div_name,
                    "wins":      stats.get("wins", "—"),
                    "losses":    stats.get("losses", "—"),
                    "pct":       stats.get("winPercent", "—"),
                    "gb":        stats.get("gamesBehind", "—"),
                    "home":      stats.get("Home", "—"),
                    "away":      stats.get("Away", "—"),
                    "conf":      stats.get("vs. Conf.", "—"),
                    "ppg":       stats.get("pointsFor", "—"),
                    "opp_ppg":   stats.get("pointsAgainst", "—"),
                    "diff":      stats.get("pointDifferential", "—"),
                    "streak":    stats.get("streak", "—"),
                    "last_10":   stats.get("Last Ten Games", "—"),
                    "ot_record": stats.get("vsOT", "—"),
                })
    return standings


def print_standings(standings: dict):
    """Pretty-print standings to console."""
    for conf, teams in standings.items():
        print(f"\n  {'─'*76}")
        print(f"  {'  ' + conf + 'ern Conference':^76}")
        print(f"  {'─'*76}")
        print(f"  {'#':<3} {'TEAM':<27} {'W':>4} {'L':>4} {'PCT':>6} {'GB':>5} {'HOME':>7} {'AWAY':>7} {'L10':>6} {'STK':>5}")
        print(f"  {'─'*76}")
        for i, t in enumerate(teams, 1):
            print(
                f"  {i:<3} {t['team']:<27} {t['wins']:>4} {t['losses']:>4} "
                f"{t['pct']:>6} {t['gb']:>5} {t['home']:>7} {t['away']:>7} "
                f"{t['last_10']:>6} {t['streak']:>5}"
            )


# ═══════════════════════════════════════════════
# SECTION 3 — TEAMS
# ═══════════════════════════════════════════════

def get_teams() -> list:
    """
    Fetch all 30 NBA teams with IDs, abbreviations, colors, and logos.

    Returns:
        List of team dicts.
    """
    data = get(f"{BASE_URL}/teams", {"limit": 40})
    if not data:
        return []

    teams = []
    for sport in data.get("sports", []):
        for league in sport.get("leagues", []):
            for team_entry in league.get("teams", []):
                t = team_entry.get("team", {})
                teams.append({
                    "id":           t.get("id"),
                    "name":         t.get("displayName"),
                    "abbreviation": t.get("abbreviation"),
                    "city":         t.get("location"),
                    "nickname":     t.get("name"),
                    "color":        t.get("color", ""),
                    "alt_color":    t.get("alternateColor", ""),
                    "logo":         next((l["href"] for l in t.get("logos", [])), None),
                })
    return teams


def get_team_info(team_id: int) -> dict:
    """
    Fetch detailed info for a single team including coach and venue.

    Args:
        team_id: ESPN team ID (from get_teams()).

    Returns:
        Dict with team details, record, coach, and arena.
    """
    data = get(f"{BASE_URL}/teams/{team_id}")
    if not data:
        return {}
    t = data.get("team", {})
    record_items = t.get("record", {}).get("items", [{}])
    return {
        "id":           t.get("id"),
        "name":         t.get("displayName"),
        "abbreviation": t.get("abbreviation"),
        "city":         t.get("location"),
        "color":        t.get("color"),
        "coach":        " ".join([c.get("firstName",""), c.get("lastName","")]).strip()
                        if t.get("coaches") else "—",
        "record":       record_items[0].get("summary", "—") if record_items else "—",
        "venue":        t.get("venue", {}).get("fullName", "—"),
        "capacity":     t.get("venue", {}).get("capacity", "—"),
    }


def get_team_roster(team_id: int) -> list:
    """
    Fetch full roster for a team including injury status.

    Args:
        team_id: ESPN team ID.

    Returns:
        List of player dicts.
    """
    data = get(f"{BASE_URL}/teams/{team_id}/roster")
    if not data:
        return []

    players = []
    for group in data.get("athletes", []):
        items = group.get("items", [group]) if isinstance(group, dict) else [group]
        for p in items:
            if "displayName" not in p:
                continue
            players.append({
                "id":         p.get("id"),
                "name":       p.get("displayName"),
                "position":   p.get("position", {}).get("abbreviation", "?"),
                "jersey":     p.get("jersey", "?"),
                "age":        p.get("age"),
                "height":     p.get("displayHeight"),
                "weight":     p.get("displayWeight"),
                "birthplace": (p.get("birthPlace") or {}).get("city", ""),
                "experience": p.get("experience", {}).get("years", 0),
                "college":    p.get("college", {}).get("name", "—"),
                "status":     p.get("status", {}).get("type", {}).get("name", "Active"),
            })
    return players


# ═══════════════════════════════════════════════
# SECTION 4 — PLAYER DATA (Enhanced)
# ═══════════════════════════════════════════════

def search_player(name: str, limit: int = 5) -> list:
    """
    Search for NBA players by name.

    Args:
        name: Player name or partial name.
        limit: Max results.

    Returns:
        List of player dicts with id, name, team, position.
    """
    data = get("https://site.web.api.espn.com/apis/common/v3/search", {
        "query": name,
        "sport": "basketball",
        "league": "nba",
        "limit": limit,
        "type": "athlete",
    })
    if not data:
        return []

    results = []
    for item in data.get("items", []):
        results.append({
            "id":       item.get("id"),
            "name":     item.get("displayName"),
            "team":     item.get("teamName"),
            "position": item.get("position"),
            "headshot": item.get("images", [{}])[0].get("url") if item.get("images") else None,
        })
    return results


def get_player_profile(player_id: int) -> dict:
    """
    Fetch full player profile — bio, team, draft info, and current status.

    Args:
        player_id: ESPN athlete ID.

    Returns:
        Dict with player bio and team info.
    """
    data = get(f"{BASE_URL}/athletes/{player_id}")
    if not data:
        return {}

    a = data.get("athlete", data)
    return {
        "id":          a.get("id"),
        "name":        a.get("displayName"),
        "first_name":  a.get("firstName"),
        "last_name":   a.get("lastName"),
        "position":    a.get("position", {}).get("displayName"),
        "jersey":      a.get("jersey"),
        "team":        a.get("team", {}).get("displayName"),
        "team_id":     a.get("team", {}).get("id"),
        "age":         a.get("age"),
        "dob":         a.get("dateOfBirth", ""),
        "birthplace":  (a.get("birthPlace") or {}).get("city", ""),
        "nationality": a.get("citizenship", ""),
        "height":      a.get("displayHeight"),
        "weight":      a.get("displayWeight"),
        "college":     a.get("college", {}).get("name", "—"),
        "draft_year":  a.get("draft", {}).get("year"),
        "draft_round": a.get("draft", {}).get("round"),
        "draft_pick":  a.get("draft", {}).get("selection"),
        "experience":  a.get("experience", {}).get("years"),
        "status":      a.get("status", {}).get("type", {}).get("name", "Active"),
        "headshot":    a.get("headshot", {}).get("href"),
    }


def get_player_season_stats(player_id: int) -> dict:
    """
    Fetch a player's current season stats (averages + totals).

    Args:
        player_id: ESPN athlete ID.

    Returns:
        Dict with 'averages' and 'totals' sub-dicts.
    """
    data = get(f"{BASE_URL}/athletes/{player_id}/statistics")
    if not data:
        return {}

    result = {"averages": {}, "totals": {}}
    for split in data.get("splits", {}).get("categories", []):
        cat_name = split.get("displayName", "")
        for stat in split.get("stats", []):
            key = stat.get("abbreviation") or stat.get("name", "")
            val = stat.get("displayValue", stat.get("value"))
            if "average" in cat_name.lower() or "per game" in cat_name.lower():
                result["averages"][key] = val
            else:
                result["totals"][key] = val
    return result


def get_player_gamelog(player_id: int, season: int = None) -> list:
    """
    Fetch a player's game-by-game log for the current (or specified) season.

    Args:
        player_id: ESPN athlete ID.
        season: Season year (e.g. 2026). Defaults to current.

    Returns:
        List of per-game stat dicts.
    """
    params = {}
    if season:
        params["season"] = season
    data = get(f"{BASE_URL}/athletes/{player_id}/gamelog", params)
    if not data:
        return []

    categories = data.get("categories", [])
    events = data.get("events", {})

    games = []
    for event_id, event_info in events.items():
        game_stats = {
            "game_id":   event_id,
            "date":      event_info.get("gameDate", ""),
            "opponent":  event_info.get("opponent", {}).get("displayName", "?"),
            "home_away": "vs" if event_info.get("homeAway") == "home" else "@",
            "result":    event_info.get("teamScore", "") + "-" + event_info.get("opponentScore", ""),
        }
        for cat in categories:
            labels = cat.get("labels", cat.get("names", []))
            for stat_event in cat.get("events", []):
                if stat_event.get("eventId") == event_id:
                    for label, val in zip(labels, stat_event.get("stats", [])):
                        game_stats[label] = val
        games.append(game_stats)

    return games


def get_player_splits(player_id: int) -> dict:
    """
    Fetch situational splits (home/away, by opponent, by month, etc.).

    Args:
        player_id: ESPN athlete ID.

    Returns:
        Dict of split categories with stat breakdowns.
    """
    data = get(f"{BASE_URL}/athletes/{player_id}/splits")
    if not data:
        return {}

    splits = {}
    for category in data.get("categories", []):
        cat_name = category.get("displayName", "unknown")
        cat_splits = []
        for split in category.get("splits", []):
            stats = {
                s.get("abbreviation", s.get("name")): s.get("displayValue")
                for s in split.get("stats", [])
            }
            cat_splits.append({"name": split.get("displayName"), "stats": stats})
        splits[cat_name] = cat_splits
    return splits


# ═══════════════════════════════════════════════
# SECTION 5 — ADVANCED ANALYTICS
# ═══════════════════════════════════════════════

def get_team_analytics(team_id: int) -> dict:
    """
    Fetch advanced team stats for the current season.
    Includes shooting splits, efficiency metrics, and pace data.

    Args:
        team_id: ESPN team ID.

    Returns:
        Flat dict of advanced metrics (name → display value).
    """
    data = get(f"{BASE_URL}/teams/{team_id}/statistics")
    if not data:
        return {}

    flat = {}
    for category in data.get("results", {}).get("stats", {}).get("categories", []):
        for stat in category.get("stats", []):
            name = stat.get("shortDisplayName") or stat.get("displayName") or stat.get("name")
            flat[name] = stat.get("displayValue", stat.get("value"))
    return flat


def get_league_leaders(stat: str = "points", limit: int = 10) -> list:
    """
    Fetch NBA statistical leaders for a given stat category.

    Args:
        stat: One of 'points', 'rebounds', 'assists', 'steals', 'blocks',
              'fieldGoalPct', 'threePointPct', 'freeThrowPct'
        limit: Number of leaders to return.

    Returns:
        List of dicts with rank, player, team, and value.
    """
    data = get(f"{BASE_URL}/leaders", {"stat": stat, "limit": limit})
    if not data:
        return []

    leaders = []
    for cat in data.get("categories", []):
        for entry in cat.get("leaders", []):
            athlete = entry.get("athlete", {})
            leaders.append({
                "rank":   entry.get("rank"),
                "player": athlete.get("displayName"),
                "team":   athlete.get("team", {}).get("abbreviation"),
                "value":  entry.get("displayValue"),
                "stat":   cat.get("displayName"),
            })
            if len(leaders) >= limit:
                break
        if leaders:
            break
    return leaders


def get_team_comparison(team_id_1: int, team_id_2: int) -> dict:
    """
    Fetch and compare analytics for two teams side by side.

    Args:
        team_id_1: ESPN team ID for first team.
        team_id_2: ESPN team ID for second team.

    Returns:
        Dict with 'team1', 'team2', and 'comparison' keys.
    """
    stats1 = get_team_analytics(team_id_1)
    stats2 = get_team_analytics(team_id_2)
    info1  = get_team_info(team_id_1)
    info2  = get_team_info(team_id_2)

    all_keys = sorted(set(stats1.keys()) | set(stats2.keys()))
    comparison = []
    for key in all_keys:
        comparison.append({
            "stat":   key,
            "team1":  stats1.get(key, "—"),
            "team2":  stats2.get(key, "—"),
        })

    return {
        "team1":      info1.get("name", f"Team {team_id_1}"),
        "team2":      info2.get("name", f"Team {team_id_2}"),
        "comparison": comparison,
    }


# ═══════════════════════════════════════════════
# SECTION 6 — INJURY REPORT
# ═══════════════════════════════════════════════

def get_injuries(team_id: int = None) -> list:
    """
    Fetch the NBA injury report.

    Args:
        team_id: Optional ESPN team ID to filter by team.
                 If None, returns all injuries league-wide.

    Returns:
        List of injury dicts with player, team, status, detail, and return date.
    """
    if team_id:
        data = get(f"{BASE_URL}/teams/{team_id}/injuries")
    else:
        data = get(f"{BASE_URL}/injuries")

    if not data:
        return []

    injuries = []
    items = data.get("items", data.get("injuries", []))

    for item in items:
        if "injuries" in item:
            team_name = item.get("team", {}).get("displayName", "Unknown")
            team_abbr = item.get("team", {}).get("abbreviation", "")
            for inj in item["injuries"]:
                injuries.append(_parse_injury(inj, team_name, team_abbr))
        else:
            injuries.append(_parse_injury(item))

    return injuries


def _parse_injury(inj: dict, team_name: str = "", team_abbr: str = "") -> dict:
    """Internal: parse a single injury entry into a clean dict."""
    athlete = inj.get("athlete", {})
    return {
        "player":      athlete.get("displayName", "Unknown"),
        "player_id":   athlete.get("id"),
        "position":    athlete.get("position", {}).get("abbreviation", "?"),
        "team":        team_name or inj.get("team", {}).get("displayName", "?"),
        "team_abbr":   team_abbr or inj.get("team", {}).get("abbreviation", "?"),
        "status":      inj.get("status", "?"),
        "type":        inj.get("type", {}).get("text", "?"),
        "detail":      inj.get("details", {}).get("detail", inj.get("longComment", "")),
        "side":        inj.get("details", {}).get("side", ""),
        "return_date": inj.get("details", {}).get("returnDate", ""),
        "date":        inj.get("date", ""),
    }


def get_injury_report_by_status() -> dict:
    """
    Fetch all injuries grouped by status (Out, Questionable, Doubtful, DTD).

    Returns:
        Dict keyed by status string, each value is a list of injury dicts.
    """
    injuries = get_injuries()
    grouped = {}
    for inj in injuries:
        status = inj.get("status", "Unknown")
        grouped.setdefault(status, []).append(inj)
    return grouped


def get_team_injury_report(team_id: int) -> list:
    """
    Convenience wrapper: fetch injuries for a single team.

    Args:
        team_id: ESPN team ID.

    Returns:
        List of injury dicts for that team.
    """
    return get_injuries(team_id=team_id)


# ═══════════════════════════════════════════════
# SECTION 7 — NEWS
# ═══════════════════════════════════════════════

def get_news(limit: int = 10, team_id: int = None) -> list:
    """
    Fetch latest NBA news from ESPN.

    Args:
        limit: Number of articles to return.
        team_id: Optional ESPN team ID for team-specific news.

    Returns:
        List of article dicts.
    """
    if team_id:
        data = get(f"{BASE_URL}/teams/{team_id}/news", {"limit": limit})
    else:
        data = get(f"{BASE_URL}/news", {"limit": limit})
    if not data:
        return []

    articles = []
    for article in data.get("articles", []):
        articles.append({
            "headline":    article.get("headline"),
            "description": article.get("description"),
            "published":   article.get("published"),
            "url":         article.get("links", {}).get("web", {}).get("href"),
            "author":      article.get("byline"),
            "categories":  [c.get("description") for c in article.get("categories", []) if c.get("description")],
        })
    return articles


# ═══════════════════════════════════════════════
# SECTION 8 — GAME SUMMARY & BOX SCORE
# ═══════════════════════════════════════════════

def get_game_summary(game_id: str) -> dict:
    """
    Fetch full game summary: box score, quarter scores, team stats, player stats.

    Args:
        game_id: ESPN event ID (from get_scoreboard()).

    Returns:
        Dict with status, quarter_scores, team_totals, player_stats, last_10_plays.
    """
    data = get(f"{BASE_URL}/summary", {"event": game_id})
    if not data:
        return {}

    header = data.get("header", {})
    comps = header.get("competitions", [{}])
    competitors = comps[0].get("competitors", []) if comps else []

    # Quarter-by-quarter scores
    linescores = {}
    for comp in competitors:
        abbr = comp.get("team", {}).get("abbreviation", "?")
        linescores[abbr] = [ls.get("displayValue", "—") for ls in comp.get("linescores", [])]

    # Team totals
    team_totals = {}
    for team_data in data.get("boxscore", {}).get("teams", []):
        abbr = team_data.get("team", {}).get("abbreviation", "?")
        stats = {s.get("label"): s.get("displayValue") for s in team_data.get("statistics", [])}
        team_totals[abbr] = stats

    # Player stats
    player_stats = {}
    for team_data in data.get("boxscore", {}).get("players", []):
        abbr = team_data.get("team", {}).get("abbreviation", "?")
        players = []
        for stat_group in team_data.get("statistics", []):
            keys = stat_group.get("labels", stat_group.get("names", []))
            for athlete in stat_group.get("athletes", []):
                a_info = athlete.get("athlete", {})
                entry = {
                    "name":         a_info.get("displayName"),
                    "position":     a_info.get("position", {}).get("abbreviation"),
                    "starter":      athlete.get("starter", False),
                    "did_not_play": athlete.get("didNotPlay", False),
                }
                entry.update(dict(zip(keys, athlete.get("stats", []))))
                players.append(entry)
        player_stats[abbr] = players

    # Last 10 plays (play-by-play)
    pbp = []
    for play in data.get("plays", [])[-10:]:
        pbp.append({
            "period":      play.get("period", {}).get("number"),
            "clock":       play.get("clock", {}).get("displayValue"),
            "description": play.get("text"),
            "score":       f"{play.get('awayScore',0)}-{play.get('homeScore',0)}",
        })

    return {
        "game_id":        game_id,
        "status":         comps[0].get("status", {}).get("type", {}).get("description", "") if comps else "",
        "quarter_scores": linescores,
        "team_totals":    team_totals,
        "player_stats":   player_stats,
        "last_10_plays":  pbp,
    }


# ═══════════════════════════════════════════════
# DEMO / MAIN
# ═══════════════════════════════════════════════

def _sep(title: str = "", width: int = 72):
    if title:
        print(f"\n{'═'*width}")
        print(f"  {title}")
        print(f"{'═'*width}")


def main():
    today     = datetime.now().strftime("%Y%m%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

    # ── 1. SCOREBOARD ──────────────────────────
    _sep("🏀  NBA SCOREBOARD")
    games = get_scoreboard(today)
    if not games:
        print(f"  No games today — showing yesterday ({yesterday}):")
        games = get_scoreboard(yesterday)
    for g in games:
        clock = f" Q{g['period']} {g['clock']}" if g['clock'] else ""
        print(f"  {g['away_team']:<28} {g['away_score']:>4}  @  "
              f"{g['home_team']:<28} {g['home_score']:<4}  [{g['status']}{clock}]")

    # ── 2. STANDINGS ───────────────────────────
    _sep("📊  NBA STANDINGS")
    standings = get_standings()
    print_standings(standings)

    # ── 3. INJURY REPORT ───────────────────────
    _sep("🚑  NBA INJURY REPORT (League-Wide)")
    injuries = get_injuries()
    if injuries:
        by_status = {}
        for inj in injuries:
            by_status.setdefault(inj["status"], []).append(inj)
        for status in ["Out", "Doubtful", "Questionable", "Day-To-Day"]:
            if status in by_status:
                print(f"\n  ── {status} ({len(by_status[status])}) ──")
                for inj in by_status[status][:10]:
                    side   = f" ({inj['side']})" if inj.get("side") else ""
                    detail = inj.get("detail") or inj.get("type", "")
                    ret    = f"  Return: {inj['return_date']}" if inj.get("return_date") else ""
                    print(f"    {inj['team_abbr']:<5} {inj['player']:<25} {inj['position']:<4} {detail}{side}{ret}")
        other = [s for s in by_status if s not in ["Out","Doubtful","Questionable","Day-To-Day"]]
        for status in other:
            print(f"\n  ── {status} ──")
            for inj in by_status[status][:5]:
                print(f"    {inj['team_abbr']:<5} {inj['player']:<25} {inj.get('detail','')}")
    else:
        print("  No injury data available (endpoint may require auth).")

    # ── 4. LEAGUE LEADERS ──────────────────────
    _sep("🏆  NBA STATISTICAL LEADERS")
    for stat_cat in ["points", "rebounds", "assists", "steals", "blocks"]:
        leaders = get_league_leaders(stat=stat_cat, limit=5)
        if leaders:
            print(f"\n  Top {stat_cat.capitalize()}:")
            for l in leaders:
                print(f"    {l.get('rank','?'):>2}. {l['player']:<26} {l['team']:<5} {l['value']}")

    # ── 5. PLAYER LOOKUP ───────────────────────
    _sep("🔍  PLAYER LOOKUP — LeBron James")
    results = search_player("LeBron James", limit=1)
    if results:
        pid     = results[0]["id"]
        profile = get_player_profile(pid)
        print(f"\n  {profile.get('name')}  #{profile.get('jersey')}  |  {profile.get('team')}  |  {profile.get('position')}")
        print(f"  Age: {profile.get('age')}   Height: {profile.get('height')}   Weight: {profile.get('weight')}")
        print(f"  Draft: {profile.get('draft_year')} Rd {profile.get('draft_round')} Pick {profile.get('draft_pick')}   Experience: {profile.get('experience')} yrs")
        print(f"  Status: {profile.get('status')}")

        stats = get_player_season_stats(pid)
        avgs  = stats.get("averages", {})
        if avgs:
            print(f"\n  Season Averages:")
            for k in ["PTS", "REB", "AST", "STL", "BLK", "FG%", "3P%", "FT%", "MIN"]:
                if k in avgs:
                    print(f"    {k:<6} {avgs[k]}")

    # ── 6. TEAM ANALYTICS SAMPLE ───────────────
    _sep("📈  TEAM ANALYTICS SAMPLE — Boston Celtics (ID: 2)")
    analytics = get_team_analytics(2)
    if analytics:
        keys_to_show = [
            "Points Per Game", "Rebounds Per Game", "Assists Per Game",
            "Field Goal Pct", "3-Point Pct", "Free Throw Pct",
            "Offensive Rating", "Defensive Rating",
        ]
        for k in keys_to_show:
            if k in analytics:
                print(f"  {k:<30} {analytics[k]}")
        if not any(k in analytics for k in keys_to_show):
            # fallback: print first 12 items
            for i, (k, v) in enumerate(analytics.items()):
                if i >= 12: break
                print(f"  {k:<30} {v}")

    # ── 7. ALL TEAMS ───────────────────────────
    _sep("🏟️   ALL 30 NBA TEAMS")
    teams = get_teams()
    for t in teams:
        print(f"  ID:{t['id']:<4} [{t['abbreviation']}] {t['name']}")

    # ── 8. SAMPLE ROSTER ───────────────────────
    _sep("📋  SAMPLE ROSTER — Los Angeles Lakers (ID: 13)")
    roster = get_team_roster(13)
    print(f"  {'#':<4} {'NAME':<26} {'POS':<5} {'HT':<8} {'WT':<8} {'AGE':<5} {'EXP':<6} {'STATUS'}")
    print(f"  {'─'*75}")
    for p in roster:
        flag = " ⚠" if p["status"] != "Active" else ""
        print(f"  {str(p['jersey']):<4} {p['name']:<26} {p['position']:<5} "
              f"{str(p['height'] or '?'):<8} {str(p['weight'] or '?'):<8} "
              f"{str(p['age'] or '?'):<5} {str(p['experience'])+'yr':<6} {p['status']}{flag}")

    # ── 9. NEWS ────────────────────────────────
    _sep("📰  LATEST NBA NEWS")
    news = get_news(limit=7)
    for article in news:
        pub = article["published"][:10] if article.get("published") else "       "
        print(f"  [{pub}] {article['headline']}")
        if article.get("url"):
            print(f"            {article['url']}")
        print()

    print(f"\n{'═'*72}")
    print("  ✅  Scrape complete — all data from ESPN's public API.")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()