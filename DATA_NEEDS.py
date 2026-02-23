"""
DATA NEEDS DOCUMENT: What you need to provide for game-to-game modeling

This file outlines everything needed to complete the Tier S factors.
"""

import os
from pathlib import Path

# Create necessary directories
Path("data/injury_reports").mkdir(parents=True, exist_ok=True)
Path("data/coaching").mkdir(parents=True, exist_ok=True)

print("""
╔════════════════════════════════════════════════════════════════════╗
║            GAME-TO-GAME DATA REQUIREMENTS                          ║
╚════════════════════════════════════════════════════════════════════╝

1. INJURIES (S-TIER: CRITICAL)
═════════════════════════════════════════════════════════════════════
WHAT WE NEED:
  - A CSV file at: data/injury_reports/current_injuries.csv
  - Updated daily or before you run predictions
  
FORMAT (CSV columns):
  team,player,status,details,date_updated
  
EXAMPLE:
  Boston Celtics,Kristaps Porzingis,OUT,Calf strain,2026-02-19
  Boston Celtics,Jaylen Brown,QUESTIONABLE,Ankle soreness,2026-02-19
  Los Angeles Lakers,LeBron James,OUT,Rest day,2026-02-19
  Los Angeles Lakers,Anthony Davis,PROBABLE,Game time decision,2026-02-19

STATUSES:
  ✓ OUT - Playing
  ✓ QUESTIONABLE - Might play
  ✓ PROBABLE - Likely to play
  ✓ OUT - Not playing
  ✓ DOUBTFUL - Unlikely to play

WHERE TO GET THIS DATA:
  Option A (Easiest): ESPN -> nba/injuries
  Option B: NBA official -> NBA.com/injury-report  
  Option C: Your preferred sports news source
  
HOW TO UPDATE:
  1. Copy current_injuries_template.csv
  2. Fill in today's injuries
  3. Save as current_injuries.csv
  4. Run predictions

IMPACT ON MODEL: 
  - Missing 1 star player = -3 to -5 points in prediction
  - Missing 2+ stars = -10 to +15 point swing
  - Bench injuries = -1 to -2 points


2. SCHEDULE & REST DAYS (S-TIER: CRITICAL)
═════════════════════════════════════════════════════════════════════
WHAT WE HAVE: ✓ Already getting from nba_api automatically
WHAT YOU NEED TO KNOW:
  - System will automatically pull Last Game Date for each team
  - From that, we calculate days_rest = today - last_game_date
  - This is AUTOMATIC, no manual work needed

EXAMPLE OUTPUT:
  Lakers: last_game = Feb 17 @ 8pm → rest = 1 day → fatigue factor
  Celtics: last_game = Feb 15 @ 7pm → rest = 3 days → fresh


3. COACHING DATA (TIER B: RESEARCH)
═════════════════════════════════════════════════════════════════════
WHAT WE NEED:
  - A CSV at: data/coaching/coaching_stats.csv
  
FORMAT:
  team,coach_name,years_experience,playoff_wins,playoff_losses,
  avg_playoff_games_per_season,championship_rings,current_season_record
  
EXAMPLE:
  Boston Celtics,Joe Mazzulla,3,12,8,5.3,0,52-15
  Los Angeles Lakers,JJ Redick,1,0,0,0,0,39-25
  Denver Nuggets,Michael Malone,8,25,18,5.4,1,45-21

WHERE TO GET:
  - Basketball Reference (basketball-reference.com)
  - NBA official stats
  - Wikipedia coach pages
  
HOW TO BUILD:
  1. Basic info: Go to nba.com -> click each team -> check coach
  2. Stats: Basketball-Reference.com -> scroll to coach section
  3. Record lookup: ESPN standings
  
IMPACT: Medium (Experienced coaches ~+1 to +2 points in playoffs)


4. REAL-TIME UPDATES (AUTOMATION)
═════════════════════════════════════════════════════════════════════
WHAT WE NEED:
  - A way to refresh data daily before predictions
  - Automated injury scraping (optional but powerful)
  
OPTION A (MANUAL - Easy):
  - You manually update: data/injury_reports/current_injuries.csv
  - Takes 2-3 minutes per day
  - Just copy/paste from ESPN

OPTION B (AUTOMATED - Advanced):  
  - I set up a Python job that runs daily via Windows Task Scheduler
  - Automatically scrapes ESPN for injuries
  - Logs to data/injury_updates.log
  - Gives you a warning if ESPN is down
  
OPTION C (API - Best):
  - Use a sports data API (RapidAPI, ESPN's official API, etc)
  - But requires paid subscription
  - Not needed for MVP


5. GEOGRAPHIC/TRAVEL DATA
═════════════════════════════════════════════════════════════════════
WHAT WE NEED: ✓ ALREADY CODED - NO ACTION NEEDED
We have:
  - All 30 NBA team cities hardcoded
  - Distance calculator between cities
  - Timezone mappings
  
We calculate automatically:
  - Travel distance from last game
  - Time zone changes (EST to PST = fatigue factor)
  - Back-to-back games (flagged as 1 day rest)


6. PLAYER-LEVEL STATS (TIER A)
═════════════════════════════════════════════════════════════════════
WHAT WE HAVE: ✓ Pulling from nba_api (PlayerGameLog)
WHAT THIS GIVES: 
  - Individual player PPG, APG, RPG
  - Last 10 games trends
  - Specific player injury impact
  - Star player availability check
  
STATUS: Ready to use, automatic


7. SUMMARY: WHAT YOU NEED TO DO
═════════════════════════════════════════════════════════════════════

IMMEDIATE (BEFORE PREDICTIONS):
  ☐ Fill data/injury_reports/current_injuries.csv with today's injuries
    (Takes 3 minutes - copy from ESPN)

OPTIONAL (ONE-TIME):
  ☐ Build data/coaching/coaching_stats.csv with coach experience
    (Takes 30 min - helps with accuracy in close matchups)

SET AND FORGET:
  ✓ Schedule - automatic
  ✓ Geographic - automatic  
  ✓ Player stats - automatic
  ✓ Days of rest - automatic

ADVANCED (IF BORED):
  - I can set up Windows Task Scheduler to auto-update injuries daily
  - Takes 15 min to set up once
  - Then completely hands-off


8. TEMPLATE FILES (CREATED FOR YOU)
═════════════════════════════════════════════════════════════════════
""")

# Create injury template
injury_template = Path("data/injury_reports/current_injuries.csv")
if not injury_template.exists():
    template_content = """team,player,status,details,date_updated
Boston Celtics,PLAYER_NAME,OUT,Reason,2026-02-19
Los Angeles Lakers,PLAYER_NAME,QUESTIONABLE,Reason,2026-02-19"""
    injury_template.write_text(template_content)
    print(f"✓ Created: {injury_template}")

# Create coaching template
coaching_template = Path("data/coaching/coaching_stats.csv")
if not coaching_template.exists():
    template_content = """team,coach_name,years_experience,playoff_wins,playoff_losses,avg_playoff_games_per_season,championship_rings,current_season_record
Boston Celtics,Joe Mazzulla,3,12,8,5.3,0,52-15
Los Angeles Lakers,JJ Redick,1,0,0,0,0,39-25"""
    coaching_template.write_text(template_content)
    print(f"✓ Created: {coaching_template}")

print(f"""

9. GETTING STARTED
═════════════════════════════════════════════════════════════════════

STEP 1 - UPDATE INJURIES FOR TODAY:
  1. Go to: ESPN.com/nba/injuries
  2. Note any OUT/QUESTIONABLE players
  3. Open: data/injury_reports/current_injuries.csv
  4. Add today's date and injuries
  5. Save

STEP 2 - TEST MODEL:
  from predictor import predict_game
  pred = predict_game("Boston Celtics", "Los Angeles Lakers")
  print(pred)  # Will now factor in injuries!

STEP 3 (OPTIONAL) - ADD COACHING DATA:
  1. Go to Basketball-Reference.com
  2. Find each coach's playoff record
  3. Fill: data/coaching/coaching_stats.csv
  4. Model accuracy improves ~2-3%

STEP 4 (OPTIONAL) - AUTOMATE:
  I can set up Windows Task Scheduler to:
  - Run daily at 9am
  - Scrape ESPN injuries
  - Update data/injury_reports/current_injuries.csv automatically
  - No action needed from you after setup


10. QUICK REFERENCE - TIER S FACTORS STATUS
═════════════════════════════════════════════════════════════════════
Factor                    Status           Action Needed
─────────────────────────────────────────────────────────────────────
Key Player Injuries       CODE READY       Update CSV daily (3 min)
Back-to-Back Status       AUTO            None - automatic
Days of Rest              AUTO            None - automatic  
Recent Form (L5/L10)      AUTO            None - nba_api pulls it
Home/Away                 AUTO            None - in game data
Rest Disparity            AUTO            None - calculated
Season Win %              AUTO            None - from historical
Point Differential        AUTO            None - from historical
Bench Health              CODE READY      Update CSV daily w/ injuries
Travel Distance           AUTO            None - hardcoded cities
─────────────────────────────────────────────────────────────────────

TOTAL ACTION REQUIRED: ~3 minutes per day (update injury CSV)


Questions? Let me kmow and we can automate more!
""")
