# Manual Data Update Guide

Since free APIs are unreliable/blocked, update these files manually:

## 1. Injuries (MOST IMPORTANT)
**File:** `data/injury_reports/manual_injuries.csv`

Get current injuries from: https://www.espn.com/nba/injuries

Format:
```
team,player,position,status,injury_type,details,date_updated
Los Angeles Lakers,LeBron James,F,Out,Ankle,Left ankle,2026-02-19
```

**Status values:** Out, Questionable, Doubtful, Day-To-Day, Out For Season

## 2. Advanced Stats (if needed)
**File:** `data/processed/team_advanced_stats.csv`

Sample data already exists. To update with real data:
- Go to: https://www.nba.com/stats/teams/advanced
- Copy team stats
- Update CSV with: team_name, wins, losses, off_rating, def_rating, net_rating, pace

## 3. Run Predictions
Once injuries are updated:
```powershell
python predict_date_range.py --start-date 2026-02-19 --end-date 2026-02-21
```

## Quick Update (5 minutes daily):
1. Open `data/injury_reports/manual_injuries.csv`
2. Check ESPN injuries page
3. Add/update any Out/Questionable players
4. Save file
5. Run predictions

The model will work with sample stats + real injuries.
