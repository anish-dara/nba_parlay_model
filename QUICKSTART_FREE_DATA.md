# 🚀 Quick Start: Free Data Collection

## Setup (One-time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify nba_api is working
python -c "from nba_api.stats.endpoints import leaguedashteamstats; print('✓ nba_api working')"
```

## Daily Data Collection

### Option 1: Run Everything at Once (Recommended)
```bash
python collect_all_data.py
```

This will collect:
- ✅ Advanced team stats (offensive/defensive ratings, pace, etc.)
- ✅ Injury reports from ESPN
- ✅ Schedule analysis (rest days, travel distance)
- ✅ Momentum and recent form

**Time:** ~2-3 minutes  
**Cost:** FREE

---

### Option 2: Run Individual Collectors

#### 1. Advanced Stats (NBA API)
```bash
python data/advanced_stats_collector.py
```
**Output:**
- `data/processed/team_advanced_stats.csv`
- `data/processed/team_shooting_stats.csv`
- `data/processed/team_clutch_stats.csv`
- `data/processed/team_last_10_games.csv`
- `data/processed/team_last_5_games.csv`

#### 2. Injury Reports (ESPN API)
```bash
python data/espn_injury_collector.py
```
**Output:**
- `data/injury_reports/current_injuries.csv`
- `data/injury_reports/injury_impact.csv`

#### 3. Schedule Analysis
```bash
python data/schedule_analyzer.py
```
**Output:**
- `data/processed/games_with_schedule.csv`

---

## What Data You Get (FREE)

### 1. Team Advanced Stats
| Stat | Description | Source |
|------|-------------|--------|
| Offensive Rating | Points per 100 possessions | nba_api |
| Defensive Rating | Points allowed per 100 poss | nba_api |
| Net Rating | Off Rating - Def Rating | nba_api |
| Pace | Possessions per game | nba_api |
| True Shooting % | Shooting efficiency | nba_api |
| Turnover % | Turnover rate | nba_api |
| Rebound % | Rebounding rate | nba_api |

### 2. Recent Form
| Stat | Description |
|------|-------------|
| Last 10 record | W-L in last 10 games |
| Last 5 record | W-L in last 5 games |
| Momentum score | -10 to +10 scale |
| Recent point diff | Avg margin last 10 |

### 3. Injuries
| Field | Description |
|-------|-------------|
| Player | Player name |
| Status | Out/Questionable/Day-to-Day |
| Injury type | Body part/condition |
| Severity score | 0-10 team impact |
| Key players out | Count of starters out |

### 4. Schedule Factors
| Factor | Description |
|--------|-------------|
| Days rest | Days since last game |
| Back-to-back | Boolean flag |
| Games in last 7 | Schedule density |
| Travel distance | Miles traveled |

---

## Data Freshness

| Data Type | Update Frequency | When to Run |
|-----------|-----------------|-------------|
| Advanced stats | Daily | Morning (after games) |
| Injuries | 2x daily | Morning + Evening |
| Schedule | Once | After collecting games |
| Momentum | Daily | After advanced stats |

**Recommended:** Run `collect_all_data.py` every morning at 9 AM

---

## Automation (Optional)

### Windows Task Scheduler
```powershell
# Create a batch file: collect_data.bat
cd C:\Users\darav\OneDrive\Desktop\nba_parlay_model
venv\Scripts\activate
python collect_all_data.py
```

Schedule to run daily at 9:00 AM

### Linux/Mac Cron
```bash
# Add to crontab
0 9 * * * cd /path/to/nba_parlay_model && source venv/bin/activate && python collect_all_data.py
```

---

## Troubleshooting

### Issue: nba_api rate limiting
**Solution:** The collectors include delays between requests. If you still hit limits, increase sleep times.

### Issue: ESPN API returns empty
**Solution:** ESPN API is unofficial and may change. Check if the endpoint is still working:
```bash
curl "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/2/injuries"
```

### Issue: No historical games found
**Solution:** Run the historical game fetcher first:
```bash
python data/fetch_historical_games.py
```

---

## Next Steps

After collecting data, you can:

1. **Train the tier-based model:**
   ```bash
   python models/tier_based_predictor.py
   ```

2. **Make predictions:**
   ```bash
   python predict_cli.py "Celtics vs Lakers"
   ```

3. **Build training dataset:**
   ```bash
   python analysis/dataset_builder.py
   ```

---

## Cost Breakdown

| Source | Cost | What You Get |
|--------|------|--------------|
| nba_api | FREE | All team stats |
| ESPN API | FREE | Injury reports |
| Schedule calc | FREE | Rest/travel data |
| Momentum calc | FREE | Form metrics |
| **TOTAL** | **$0/month** | **50+ factors** |

---

## Data Quality

### ✅ High Quality (Reliable)
- Team stats from nba_api
- Game results
- Schedule calculations

### ⚠️ Medium Quality (Unofficial)
- ESPN injury API (can break)
- Travel distance (estimated)

### 📝 Manual Entry Needed
- Coaching stats (win %, experience)
- Motivation factors (rivalry games)
- ATS records (requires scraping)

---

## Support

If you encounter issues:
1. Check logs in console output
2. Verify internet connection
3. Ensure nba_api is up to date: `pip install --upgrade nba_api`
4. Check if NBA API is down: https://stats.nba.com/

---

## What's Next?

Once you have data collected, see:
- `TIER_MODEL_SUMMARY.md` - How to use the tier-based model
- `DATA_SOURCES.md` - Additional data sources (paid options)
- `models/tier_based_predictor.py` - Prediction engine
