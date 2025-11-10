# Local Testing Guide

## Step-by-Step: Test CasualHero BI App Locally

### Prerequisites

1. **Database connection configured** - `.env` file with `DATABASE_URL`
2. **Python environment ready** - Python 3.11+
3. **Dependencies installed** - All packages from `requirements.txt`

---

## Step 1: Install/Update Dependencies

```bash
# Navigate to project
cd "C:\Users\azimu\Documents\012. Casual Hero"

# Install/update all dependencies
pip install -r requirements.txt
```

Expected output: All packages installed successfully

---

## Step 2: Verify Database Connection

```bash
# Quick test of database connection
python -c "from src.data.connector import get_db; db = get_db(); print('✓ Database connected')"
```

Expected output: `✓ Database connected`

If this fails, check:
- `.env` file exists with correct `DATABASE_URL`
- AWS RDS is accessible
- Credentials are correct

---

## Step 3: Start Streamlit App

```bash
# Run the app
streamlit run src/ui/app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**What happens on first run:**
- App starts (~2 seconds)
- First page load triggers data loading (~40-60 seconds)
  - Queries AWS PostgreSQL for 5 years of data
  - Prepares data with fiscal calendar
  - Caches in memory
- Shows home page with data summary

**Browser should auto-open to:** http://localhost:8501

---

## Step 4: Verify App Loads

**You should see:**

1. **Home Page Title:** "🏠 CasualHero BI Platform"

2. **Sidebar:**
   - Navigation: Home, Weekly Report, Monthly Report, Trends
   - Admin Controls (collapsed)
   - Data summary (rows, establishments, date range)

3. **Main Content:**
   - Welcome message
   - Current fiscal period (e.g., "FY2026 Week 5")
   - Quick stats (Total Orders, Total Sales, Establishments)

4. **Loading Spinner (first time only):**
   - "Loading transaction data..." (~40-60 seconds)
   - Then data displays instantly

**Expected first load:**
```
Loading transaction data...
[40-60 seconds with spinner]
✓ Data loaded: 322,481 transactions
✓ 17 establishments
✓ Date range: 2023-10-02 to 2025-11-02
```

---

## Step 5: Test Caching (Second Load)

1. **Refresh browser (F5)**
2. **Expected:** Page loads INSTANTLY (no 40-60s wait)
3. **Why?** Data cached via `@st.cache_resource`

This proves the caching strategy works!

---

## Step 6: Test Admin Controls

1. **Expand "Admin Controls" in sidebar**
2. **Click "🔄 Reload Data"**
3. **Expected:** Cache clears, data reloads (~40-60s), then instant again

This is the manual refresh button for mid-day updates.

---

## Step 7: Test Navigation

Click through pages in sidebar:

1. **Home** - Should show welcome page ✓
2. **Weekly Report** - Shows "Coming soon..." (we'll build this next)
3. **Monthly Report** - Shows "Coming soon..."
4. **Trends** - Shows "Coming soon..."

---

## Troubleshooting

### Issue: Database connection error

**Error:** `Connection failed` or `DATABASE_URL not set`

**Fix:**
```bash
# Check .env file
cat .env | grep DATABASE_URL

# Should show:
# DATABASE_URL=postgresql://...

# If missing, create .env:
cp .env.example .env
# Then edit with correct credentials
```

### Issue: Import errors

**Error:** `ModuleNotFoundError: No module named 'streamlit'`

**Fix:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install missing package directly
pip install streamlit
```

### Issue: Slow data load (>2 minutes)

**Possible causes:**
- Large dataset (expected for 5 years)
- Slow network to AWS RDS
- Database query performance

**Check:**
```python
# Test query speed directly
python scripts/fetch_week4_data.py
# Should complete in 30-60 seconds
```

### Issue: Port 8501 already in use

**Error:** `Address already in use`

**Fix:**
```bash
# Kill existing Streamlit process
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Or use different port:
streamlit run src/ui/app.py --server.port=8502
```

### Issue: Data shows as empty

**Symptoms:**
- No errors
- Stats show "0 orders"
- Date range missing

**Fix:**
```bash
# Check data exists in database
python scripts/check_sample_data.py

# Verify fiscal calendar config
python -c "from src.core.fiscal_calendar import get_configured_years; print(get_configured_years())"
```

---

## Success Checklist

After testing, you should have verified:

- [x] App starts without errors
- [x] First load takes 40-60 seconds (expected - data loading)
- [x] Second load is INSTANT (cache working)
- [x] Home page shows correct data:
  - [ ] Total orders (should be ~216,056 from test data)
  - [ ] Total sales (should be ~£1.7M)
  - [ ] 17 establishments
- [x] Sidebar navigation works
- [x] Admin reload button clears cache and reloads
- [x] No errors in terminal

---

## Next Steps

Once local testing passes:

1. **Build Weekly Report page** (next task)
2. **Test cache warmer** (optional):
   ```bash
   # In separate terminal:
   python scripts/test_cache_warmer_local.py
   ```
3. **Deploy to Fly.io** (after UI complete)

---

## Quick Reference

```bash
# Start app
streamlit run src/ui/app.py

# Stop app
Ctrl+C in terminal

# View logs
# (Shown in terminal where Streamlit is running)

# Test database
python -c "from src.data.connector import get_db; get_db().test_connection()"

# Test fiscal calendar
python src/core/fiscal_calendar.py
```
