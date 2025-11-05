# CasualHero BI Platform - Development Context

## Project Overview
Replace Power BI dashboards (£500/month) with custom Streamlit solution.
- Customer: Snowflake Gelato (15 locations)
- Timeline: 2-3 weeks to MVP
- Clean break from Power BI (no dependency)
- Target cost should not exceed £100/month. Ideally sticking to £30/month

## Tech Stack
- Frontend: Streamlit
- Data Processing: Polars + DuckDB
- Database: PostgreSQL (AWS initially, Neon long-term)
- Deployment: Fly.io
- Language: Python 3.11+
- NO Next.js/Vercel (principle)

## Database Migration Strategy

### Phase 1: AWS PostgreSQL (Current/MVP)
**Initial Setup (2-3 weeks):**
- Connect to existing AWS PostgreSQL instance
- Use existing materialized view (already created)
- Treat as "black box" - query the view, get data
- Focus on building Streamlit UI and recreating Power BI dashboards

**Why this approach:**
- Fast MVP delivery (no database work needed)
- Client already has AWS infrastructure
- Materialized view already optimized
- Low risk - proven data source

### Phase 2: Reverse Engineering (Post-MVP)
**Gradual Migration:**
- Reverse engineer the materialized view logic
- Understand the transformations and aggregations
- Document the SQL queries and business rules
- Recreate logic in Polars/DuckDB (Python-native)

**Goals:**
- Understand what the view does
- Identify optimization opportunities
- Prepare for Neon migration

### Phase 3: Neon Migration (Future)
**Long-term Target:**
- Migrate to Neon Serverless PostgreSQL
- Implement materialized view logic in application layer (Polars/DuckDB)
- Cost optimization (Neon's pay-per-use model)
- Better control over data transformations

**Benefits:**
- Lower monthly costs (target: £30/month total)
- Serverless scaling
- Simplified infrastructure
- More flexible data processing

### Connection Architecture
**connector.py must support BOTH:**
```python
# Phase 1: AWS PostgreSQL
DATABASE_URL=postgresql://user:pass@aws-instance:5432/db

# Phase 3: Neon PostgreSQL
DATABASE_URL=postgresql://user:pass@neon-instance:5432/db
```

**Key Principle:** Same connector code works for both - just swap DATABASE_URL

## Critical Business Rules

### 7AM Cutoff Rule
Transactions before 7:00 AM count as PREVIOUS day.
```python
def adjust_for_cutoff(timestamp: datetime, cutoff_hour: int = 7) -> date:
    if timestamp.hour < cutoff_hour:
        return (timestamp - timedelta(days=1)).date()
    return timestamp.date()
```

### Fiscal Calendar - Manual Override Approach
Fiscal Year: October 1 - September 30
Weeks: Monday - Sunday

**Manual overrides (from Power BI DAX):**
```python
FISCAL_OVERRIDES = {
    2024: date(2023, 10, 2),   # Oct 1, 2023 is Sunday → Week 1 starts Oct 2
    2025: date(2024, 9, 30),   # Oct 1, 2024 is Tuesday → Week 1 starts Sep 30
    # Add more years as needed
}
```

**Rule Pattern:**
- Just follow FISCAL_OVERRIDES rules

### Week/Year Boundary Logic
```
FY2024 (Oct 1, 2023 is Sunday):
└── Week 1: Oct 2 - Oct 8
└── Sep 25 - Oct 1 is FY2023 Week 52/53

FY2025 (Oct 1, 2024 is Tuesday):
└── Week 1: Sep 30 - Oct 6
└── Sep 30 is in FY2025 (!)
```

## Data Model

### Current State (Phase 1)
**AWS PostgreSQL Materialized View:**
- Name: [TBD - need from client]
- Structure: [TBD - need schema from client]
- Refresh Schedule: [TBD - need from client]
- Contains: Pre-aggregated transaction data with fiscal calculations

**Initial Approach:**
- Query the materialized view directly
- No need to understand underlying tables initially
- Focus on SELECT queries only
- Reverse engineer structure as we build dashboards

### Required Information (from client):
1. Materialized view name
2. Column names and data types
3. Sample data (10-20 rows)
4. Refresh frequency
5. AWS connection details (host, port, credentials)

## DAX Measures to Recreate
[PENDING - Need 3-5 examples from user]

Key measure types:
- YTD calculations
- YoY comparisons
- Budget variance
- Fiscal week aggregations
- Time intelligence functions

## Reports to Build

### Weekly Report (5 pages)
- Power BI matrices to recreate
- [Structure TBD]

### Monthly Report (5-6 pages)
- Power BI matrices to recreate
- [Structure TBD]

## Development Approach
- Skip heavy SDLC for MVP
- Build → Test → Deploy iteratively
- Production-grade code from start
- Separation of concerns (UI-agnostic business logic)
- Type hints everywhere
- Test fiscal calendar against Power BI outputs

## Project Structure
```
casualhero/
├── src/
│   ├── core/
│   │   ├── fiscal_calendar.py    # Fiscal year/week calculations
│   │   └── kpi_calculator.py     # DAX → Polars translations
│   ├── data/
│   │   ├── connector.py          # Database connection
│   │   └── queries.py            # SQL queries
│   ├── ui/
│   │   ├── pages/
│   │   │   ├── weekly_report/    # 5 pages
│   │   │   └── monthly_report/   # 5-6 pages
│   │   └── app.py                # Main Streamlit app
│   └── config/
│       └── settings.py           # Configuration
├── tests/
│   ├── test_fiscal_calendar.py   # CRITICAL: Validate against Power BI
│   └── test_kpi_calculator.py
├── claude.md                      # This file
├── requirements.txt
├── Dockerfile
└── README.md
```

## Current Status - Week 1 Progress

### ✅ COMPLETED (Session 1 - Nov 4, 2025)

**1. Fiscal Calendar Module** (`src/core/fiscal_calendar.py`)
- ✅ Config-driven approach (YAML file, not hardcoded)
- ✅ `adjust_for_cutoff(timestamp)` - 7AM cutoff rule implemented
- ✅ `get_week1_start(fiscal_year)` - Lookup from config
- ✅ `get_fiscal_year(date)` - Determine fiscal year
- ✅ `get_fiscal_week(date)` - Calculate week number (1-52/53)
- ✅ `get_fiscal_info(date)` - Comprehensive fiscal data
- ✅ TESTED: FY2024 boundaries, 7AM cutoff working correctly
- ✅ Production-ready: type hints, docstrings, error handling

**2. Fiscal Calendar Configuration** (`config/fiscal_overrides.yaml`)
- ✅ FY2024, FY2025, FY2026 configured
- ✅ Protected config file (client-controlled, not developer-controlled)
- ✅ Week 1 start dates defined
- ✅ Comments and documentation included

**3. Database Connector** (`src/data/connector.py`)
- ✅ SQLAlchemy-based connection management
- ✅ Supports BOTH AWS PostgreSQL AND Neon (same code)
- ✅ Connection pooling (configurable: 10 connections, 20 overflow)
- ✅ SSL/TLS support (required for AWS RDS and Neon)
- ✅ Context managers for safe transactions
- ✅ Error handling with helpful messages
- ✅ Singleton pattern with `get_db()` function

**4. Query Module** (`src/data/queries.py`)
- ✅ Template functions for materialized view queries
- ✅ Returns Polars DataFrames (not pandas)
- ✅ Fiscal calendar integration (auto-adds fiscal year/week columns)
- ✅ Schema discovery functions (`get_view_schema()`)
- ✅ Ready to update once client provides schema

**5. Configuration & Security**
- ✅ `.env.example` - Complete template for AWS and Neon
- ✅ `.gitignore` - Protects credentials and sensitive data
- ✅ `requirements.txt` - All dependencies listed (Polars, DuckDB, SQLAlchemy, PyYAML, etc.)
- ✅ Security best practices documented

**6. Project Structure**
- ✅ `src/core/` - Business logic (fiscal calendar)
- ✅ `src/data/` - Database layer (connector, queries)
- ✅ `config/` - Configuration files (fiscal overrides)

### 🔄 IN PROGRESS

**Waiting on Client (Expected Tomorrow):**
1. AWS PostgreSQL connection details
   - Host, port, database name
   - Username/password (read-only user preferred)
   - Security group configured for developer IP
2. Materialized view details
   - View name
   - Column schema (names and data types)
   - Sample data (10-20 rows)
   - Refresh schedule

### ⏳ NEXT STEPS (Once AWS Credentials Received)

**Phase 1A: Connect to AWS Database**
1. Test database connection
2. Discover materialized view schema
3. Update query functions with actual column names
4. Pull sample data and validate structure

**Phase 1B: Build KPI Calculator**
1. Get 3-5 DAX measure examples from client
2. Create `src/core/kpi_calculator.py`
3. Translate DAX logic to Polars/DuckDB
4. Validate calculations against Power BI outputs

**Phase 1C: Build Streamlit Dashboard**
1. Get Power BI dashboard screenshots
2. Create `src/ui/app.py` (main Streamlit app)
3. Implement weekly report (5 pages)
4. Implement monthly report (5-6 pages)
5. Deploy to Fly.io

**Phase 1D: MVP Delivery (Target: 2-3 weeks)**
- Full like-for-like replacement of Power BI dashboards
- Validated against Power BI outputs
- Running on Fly.io
- Client testing and feedback

## Testing Requirements
All fiscal calendar calculations MUST match Power BI exactly.

Test cases needed:
- FY2024 boundaries
- FY2025 boundaries
- 7AM cutoff scenarios
- Edge cases (Oct 1, Sep 30)

## Key Decisions & Notes

### Design Decisions Made
1. **Fiscal calendar is CONFIG-DRIVEN**
   - Client controls fiscal year dates via YAML (not developers)
   - No hardcoded business logic for date calculations
   - Protected config file (restricted access)
   - Fail-fast if fiscal year not configured

2. **Database Connector is MIGRATION-READY**
   - Same code works for AWS PostgreSQL and Neon
   - Just swap DATABASE_URL environment variable
   - SSL/TLS enabled by default (required for both AWS and Neon)
   - Connection pooling optimized for cloud databases

3. **Query Module Uses POLARS (not pandas)**
   - 5-10x faster for 5-10M row datasets
   - Lower memory footprint
   - Lazy evaluation support
   - Better type system

4. **Security Best Practices**
   - All credentials in .env file (never in code)
   - .env is gitignored (won't be committed)
   - .env.example provides template
   - AWS connection should use read-only database user

### Business Context
- Customer: Snowflake Gelato (15 locations)
- Good relationship, low-risk trial
- Timeline: 2-3 weeks to MVP
- Cost target: £30/month ideal, £100/month max
- Focus: Like-for-like Power BI replacement first
- Must validate all calculations against Power BI outputs

### Critical Rules Implemented
- ✅ Fiscal Year: October 1 - September 30
- ✅ Weeks: Monday - Sunday
- ✅ 7AM Cutoff: Transactions before 7am count as previous day
- ✅ Week 1 can start in late September
- ✅ Sep 30 can be in new fiscal year (e.g., FY2025)

---

## How to Resume Work

When you return to this project:

1. **Open VS Code** to this folder
2. **Open Claude Code** (Ctrl+Shift+P → "Claude Code")
3. **Say**: "Read CLAUDE.md and let's continue where we left off"

Claude will automatically read this file and understand the full context!

---

**Last Updated:** Nov 4, 2025 - Session 1
**Next Session:** Connect to AWS database and discover materialized view schema