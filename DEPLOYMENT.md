# Deployment Guide - Fly.io

## Overview

This guide covers deploying the CasualHero BI Platform to Fly.io with:
- 8GB RAM instance (London region)
- Scheduled cache warming at 9:25 AM daily
- 24-hour data caching with instant user experience
- Always-on configuration (no auto-sleep)

---

## Prerequisites

1. **Fly.io Account**
   - Sign up at https://fly.io/
   - Install flyctl CLI: https://fly.io/docs/hands-on/install-flyctl/

2. **Database Credentials**
   - AWS RDS PostgreSQL connection string
   - Format: `postgresql://username:password@host:port/database`

3. **Application Ready**
   - All code committed to git
   - `requirements.txt` up to date
   - `Dockerfile` configured
   - `fly.toml` configured

---

## Initial Deployment

### Step 1: Install Fly CLI

```bash
# Windows (PowerShell)
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Verify installation
flyctl version
```

### Step 2: Login to Fly.io

```bash
flyctl auth login
```

### Step 3: Launch App

```bash
# Navigate to project root
cd "C:\Users\azimu\Documents\012. Casual Hero"

# Launch app (follows fly.toml configuration)
flyctl launch --no-deploy

# This will:
# - Create app "casualhero-bi"
# - Set region to "lhr" (London)
# - Configure 8GB RAM
# - NOT deploy yet (we need to set secrets first)
```

### Step 4: Set Secrets (Database Credentials)

```bash
# Set DATABASE_URL (replace with actual credentials)
flyctl secrets set DATABASE_URL="postgresql://user:pass@host:5432/snowflake_sftp"

# The app will restart after setting secrets
```

### Step 5: Deploy Application

```bash
# Deploy for the first time
flyctl deploy

# This will:
# - Build Docker image
# - Push to Fly.io registry
# - Start app instance
# - Run cache warmer at 9:25 AM daily
```

### Step 6: Verify Deployment

```bash
# Check app status
flyctl status

# View logs
flyctl logs

# Open app in browser
flyctl open
```

---

## Configuration Files

### fly.toml

Key configurations:

```toml
app = "casualhero-bi"
primary_region = "lhr"  # London

[vm]
  cpus = 2
  memory = "8gb"

[[services.cron]]
  schedule = "25 8 * * *"  # 8:25 AM UTC = 9:25 AM BST
  command = "python scripts/cache_warmer.py --prod"
```

**Timezone Note:**
- UK is UTC+0 (winter GMT) or UTC+1 (summer BST)
- Schedule set for 8:25 AM UTC to match 9:25 AM BST
- Adjust if client is always GMT (no DST)

### Dockerfile

Builds Python 3.11 slim image with:
- Streamlit
- Polars
- SQLAlchemy
- All requirements

### Cache Warmer

Location: `scripts/cache_warmer.py`

**What it does:**
- Runs at 9:25 AM daily (before users arrive)
- Hits app endpoints to trigger cache loading
- Pre-loads 5 years of data (~40 seconds)
- Pre-calculates current week + last 4 weeks (~20 seconds)
- Result: All users get instant experience

---

## Daily Operation

### Timeline

```
9:00 AM  - AWS RDS materialized view refreshed (client's process)
9:25 AM  - Cache warmer starts (Fly.io cron)
9:26 AM  - Cache ready (60 seconds total)
9:30 AM+ - Users arrive → INSTANT experience
All day  - All users → INSTANT (app-level cache)
```

### Cache Lifecycle

1. **9:25 AM:** Cron triggers `cache_warmer.py`
2. **9:25:00-9:25:40:** Data loads from AWS (40s)
3. **9:25:40-9:26:00:** Reports pre-calculated (20s)
4. **9:26 AM:** Cache ready
5. **All day:** Cache valid (24-hour TTL)
6. **Next day 9:25 AM:** Repeat

### Manual Cache Refresh

If mid-day data reload needed:

```bash
# SSH into instance
flyctl ssh console

# Run cache warmer manually
python scripts/cache_warmer.py --prod

# OR use Admin button in Streamlit UI (easier)
```

---

## Monitoring

### View Logs

```bash
# Real-time logs
flyctl logs

# Filter by type
flyctl logs --region lhr

# Last 100 lines
flyctl logs --limit 100
```

### Check Cache Warmer

```bash
# Look for cache warmer logs
flyctl logs | grep "CACHE WARMER"

# Should see:
# [09:25:00] CACHE WARMER STARTED
# [09:26:00] CACHE WARMER COMPLETE
```

### Check App Health

```bash
# Status check
flyctl status

# Should show:
# - 1 instance running
# - Status: healthy
# - Region: lhr
```

---

## Scaling

### Increase RAM (if needed)

```bash
# Scale to 16GB (if 8GB insufficient)
flyctl scale memory 16384

# Check current resources
flyctl scale show
```

### Add Regions (for redundancy)

```toml
# Edit fly.toml
[regions]
  lhr = ["lhr"]  # London (primary)
  ams = ["ams"]  # Amsterdam (backup)
```

```bash
# Deploy changes
flyctl deploy
```

---

## Troubleshooting

### Cache Warmer Not Running

**Check cron schedule:**
```bash
flyctl ssh console
cat /fly.toml | grep schedule
```

**Verify timezone:**
- 8:25 AM UTC = 9:25 AM BST (summer)
- 9:25 AM UTC = 9:25 AM GMT (winter)

**Test manually:**
```bash
flyctl ssh console
python scripts/cache_warmer.py --prod
```

### Slow Data Load

**Check AWS RDS:**
- Is materialized view refreshed?
- Network latency from London → eu-west-2 AWS?

**Check query performance:**
```bash
flyctl ssh console
python
>>> from src.data.connector import get_db
>>> from src.data.queries import query_all_transactions
>>> import time
>>> start = time.time()
>>> df = query_all_transactions(get_db(), years=5)
>>> print(f"Loaded {len(df):,} rows in {time.time()-start:.1f}s")
```

### Out of Memory

**Symptoms:**
- App crashes at 9:25 AM
- Logs show "OOMKilled"

**Solution:**
```bash
# Increase RAM
flyctl scale memory 16384  # 16GB

# Or reduce years loaded
# Edit src/ui/app.py: load_transactions(years=3)
```

### Database Connection Failed

**Check secrets:**
```bash
flyctl secrets list

# Should show:
# DATABASE_URL | <redacted>
```

**Test connection:**
```bash
flyctl ssh console
python -c "from src.data.connector import get_db; get_db().test_connection()"
```

---

## Cost Estimation

### Current Configuration

```
VM: 8GB RAM, 2 vCPUs, London region
- Instance: ~£20/month
- Network: ~£2/month (EU region)
- Total: ~£22/month
```

### Phase 3 (Neon Migration)

```
Fly.io: 8GB RAM
- Instance: ~£20/month

Neon PostgreSQL:
- Storage: ~£8/month (15GB)
- Compute: ~£2/month (serverless)
- Total: ~£10/month

Combined: ~£30/month ✅ (Target achieved!)
```

---

## Deployment Checklist

Before deploying:

- [ ] `fly.toml` configured (app name, region, RAM)
- [ ] `Dockerfile` tested locally
- [ ] `requirements.txt` up to date
- [ ] `.gitignore` includes `.env` (no credentials in git)
- [ ] `.env.example` updated with all required variables
- [ ] Cache warmer script tested
- [ ] Database credentials ready
- [ ] Fly.io account created and CLI installed

Deploy:

- [ ] `flyctl launch --no-deploy`
- [ ] `flyctl secrets set DATABASE_URL="..."`
- [ ] `flyctl deploy`
- [ ] `flyctl open` (verify app loads)
- [ ] Check logs: `flyctl logs`
- [ ] Wait for 9:25 AM, verify cache warmer runs
- [ ] Test user experience at 9:30 AM+

---

## Useful Commands

```bash
# Deployment
flyctl deploy                    # Deploy updates
flyctl deploy --remote-only      # Build on Fly.io (not local)

# Monitoring
flyctl logs                      # View logs
flyctl status                    # Check app health
flyctl scale show                # Show current resources

# Management
flyctl ssh console               # SSH into instance
flyctl secrets list              # List secrets
flyctl secrets set KEY=value     # Set secret
flyctl restart                   # Restart app

# Scaling
flyctl scale memory 8192         # Set RAM (MB)
flyctl scale count 2             # Set instance count

# Cleanup
flyctl apps destroy casualhero-bi  # Delete app (careful!)
```

---

## Support

- **Fly.io Docs:** https://fly.io/docs/
- **Fly.io Community:** https://community.fly.io/
- **Streamlit Docs:** https://docs.streamlit.io/
- **Project Issues:** [GitHub repo - TBD]

---

## Next Steps

After initial deployment:

1. **Monitor first day:**
   - Watch cache warmer at 9:25 AM
   - Check user experience at 9:30 AM+
   - Review logs for errors

2. **Optimize:**
   - Tune cache TTL if needed
   - Adjust cron schedule for timezone
   - Monitor RAM usage (scale if needed)

3. **Build features:**
   - Complete Weekly Report page
   - Add Monthly Report page
   - Implement drill-down functionality

4. **Plan Phase 2:**
   - Migrate to Neon (cost savings)
   - Implement Toast SFTP ingestion
   - Add incremental data refresh
