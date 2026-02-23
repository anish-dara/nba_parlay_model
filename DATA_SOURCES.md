# Data Sources Required for Tier-Based NBA Prediction Model

## 📊 Current Data Sources (Already Available)

### 1. **nba_api** (Already in requirements.txt)
- ✅ Basic game scores and results
- ✅ Team records
- ✅ Basic box scores

**What's Missing:**
- Advanced stats (offensive/defensive ratings)
- Player-level injury data
- Detailed shooting splits

---

## 🔴 CRITICAL: New Data Sources Needed

### 2. **NBA Stats API (stats.nba.com)** - FREE
**Endpoint:** `https://stats.nba.com/stats/`

**What it provides:**
- ✅ Offensive/Defensive ratings
- ✅ Net rating
- ✅ Pace
- ✅ True shooting %
- ✅ Turnover rate
- ✅ Rebound rate
- ✅ Clutch stats (games within 5 pts in last 5 min)
- ✅ Home/Away splits

**Implementation:**
```python
from nba_api.stats.endpoints import teamdashboardbygeneralsplits, leaguedashteamstats

# Get advanced team stats
team_stats = leaguedashteamstats.LeagueDashTeamStats(
    season='2024-25',
    measure_type_detailed_defense='Advanced'
).get_data_frames()[0]
```

**Status:** ✅ Can use existing `nba_api` library

---

### 3. **Injury Data** - REQUIRED
**Options:**

#### Option A: ESPN API (Unofficial, FREE)
```
https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/injuries
```
- ✅ Current injury status
- ✅ Player names
- ✅ Injury type
- ❌ No historical data
- ❌ Unofficial (could break)

#### Option B: RotoWire (PAID - $50-100/month)
```
https://www.rotowire.com/basketball/nba-lineups.php
```
- ✅ Real-time injury updates
- ✅ Probable/Questionable/Out status
- ✅ Historical injury data
- ✅ Reliable

#### Option C: Web Scraping (FREE but fragile)
- Scrape from ESPN, CBS Sports, or NBA.com
- ⚠️ Requires maintenance when sites change

**Recommendation:** Start with ESPN API, upgrade to RotoWire if serious

---

### 4. **Rest & Schedule Data** - PARTIALLY AVAILABLE
**Source:** NBA Schedule API (FREE)
```
https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json
```

**What it provides:**
- ✅ Game dates/times
- ✅ Home/away
- ✅ Can calculate days rest
- ❌ No travel distance

**For Travel Distance:**
- Need to calculate manually using team city coordinates
- Use `geopy` library (FREE)

---

### 5. **Coaching Stats** - MANUAL/SCRAPED
**Sources:**
- Basketball-Reference.com (scraping required)
- NBA.com coach pages

**What's needed:**
- Coach win percentage
- Years of experience
- Playoff record

**Status:** ⚠️ Requires web scraping or manual entry

---

### 6. **Against The Spread (ATS) Data** - PAID
**Sources:**

#### Option A: Covers.com (FREE with scraping)
```
https://www.covers.com/sport/basketball/nba/teams/main
```
- ✅ ATS records
- ✅ Over/Under records
- ❌ Requires scraping

#### Option B: The Odds API (PAID - $50-200/month)
```
https://the-odds-api.com/
```
- ✅ Historical odds
- ✅ ATS calculations
- ✅ Multiple bookmakers
- ✅ API access

**Status:** ⚠️ Already using The Odds API for live odds (see `data/collector.py`)

---

### 7. **Player Minutes & Usage** - AVAILABLE
**Source:** nba_api
```python
from nba_api.stats.endpoints import teamplayerdashboard

# Get player minutes and usage
player_stats = teamplayerdashboard.TeamPlayerDashboard(
    team_id='1610612738',  # Celtics
    season='2024-25'
).get_data_frames()[0]
```

**Status:** ✅ Can implement with existing library

---

### 8. **Momentum & Streaks** - CALCULATED
**Source:** Derived from game results
- Calculate from historical games
- No external API needed

**Status:** ✅ Can calculate internally

---

## 📋 Implementation Priority

### Phase 1: IMMEDIATE (Use existing data)
1. ✅ Basic team stats (nba_api)
2. ✅ Win/loss records
3. ✅ Home/away splits
4. ✅ Recent form (L5, L10)
5. ✅ Days rest (from schedule)

### Phase 2: HIGH PRIORITY (1-2 weeks)
1. 🔴 Advanced stats (offensive/defensive rating) - nba_api
2. 🔴 Injury data - ESPN API (free) or manual CSV
3. 🔴 Player minutes/usage - nba_api
4. 🔴 Pace and efficiency stats - nba_api

### Phase 3: MEDIUM PRIORITY (1 month)
1. 🟡 Travel distance calculations - geopy
2. 🟡 Coaching stats - manual entry or scraping
3. 🟡 Clutch stats - nba_api
4. 🟡 Three-point shooting splits - nba_api

### Phase 4: NICE TO HAVE (2+ months)
1. 🟢 ATS records - scraping or paid API
2. 🟢 Historical injury impact analysis
3. 🟢 Referee data
4. 🟢 Weather (for outdoor events, N/A for NBA)

---

## 💰 Cost Breakdown

### FREE Option (Recommended for MVP):
- nba_api: FREE
- ESPN injury API: FREE (unofficial)
- Manual coaching data: FREE (time investment)
- Basic calculations: FREE

**Total: $0/month**

### PAID Option (Professional):
- The Odds API: $50-200/month (already using)
- RotoWire injuries: $50-100/month
- SportsRadar (comprehensive): $500-2000/month

**Total: $100-2200/month**

---

## 🚀 Quick Start Implementation

### Step 1: Install additional dependencies
```bash
pip install geopy beautifulsoup4 requests-cache
```

### Step 2: Create data collectors
```python
# data/advanced_stats_collector.py
# data/injury_collector.py  (already have basic version)
# data/schedule_analyzer.py
```

### Step 3: Update feature engineering
```python
# analysis/tier_feature_engineering.py
# Integrate all 50+ factors
```

### Step 4: Train tier-based model
```python
# Use tier_based_predictor.py as the new prediction engine
```

---

## 📝 Data Update Frequency

| Data Type | Update Frequency | Source |
|-----------|-----------------|--------|
| Game results | Daily | nba_api |
| Injuries | 2x daily | ESPN API |
| Advanced stats | Daily | nba_api |
| Odds | Real-time | The Odds API |
| Coaching | Weekly | Manual |
| ATS records | Daily | Scraping |

---

## ⚠️ Current Limitations

1. **No real-time injury severity** - Need manual assessment or paid service
2. **No referee data** - Would require scraping
3. **No player prop data** - Would need separate API
4. **No lineup data** - Starting lineups not available until ~30 min before game
5. **No weather** - N/A for indoor NBA games

---

## 🎯 Recommended Approach

**For MVP (Minimum Viable Product):**
1. Use nba_api for all team stats (FREE)
2. Manual injury CSV updates daily (FREE)
3. Calculate rest/schedule from game data (FREE)
4. Use existing The Odds API for betting lines (CURRENT)

**For Production:**
1. Add RotoWire for injuries ($50/mo)
2. Add automated scraping for ATS data (FREE but maintenance)
3. Consider SportsRadar for comprehensive data ($500+/mo)

**Total MVP Cost: $0/month (just time)**
**Total Production Cost: $50-100/month**
