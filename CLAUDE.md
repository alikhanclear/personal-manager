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

### ✅ COMPLETED (Session 2 - Nov 5, 2025)

**1. AWS Database Connection**
- ✅ Connected to AWS RDS PostgreSQL 15.12
- ✅ Database: `snowflake_sftp`
- ✅ Endpoint: `snowflake-gelato-db-restored.c31jl8xofey0.eu-west-2.rds.amazonaws.com`
- ✅ SSL/TLS connection working
- ✅ Password URL-encoding for special characters

**2. Materialized View Discovery**
- ✅ Found view: `public.mv_item_details`
- ✅ Schema discovered (11 columns)
- ✅ Connection test successful
- ✅ Sample data queried

**3. Schema: `mv_item_details`**

| Column | Type | Description |
|--------|------|-------------|
| Establishment | text | Location/store name |
| Order_Number | bigint | Unique order ID |
| Order_Date | timestamp without time zone | Order timestamp |
| Clean_Product_Name | text | Product name |
| Clean_Class | text | Product category |
| Total_Sales_Actual | numeric | Total sales (with tax) |
| Net_Sales_Actual | numeric | Net sales (before tax) |
| Product_Quantity | integer | Quantity sold |
| Total_Product_Tax | numeric | Tax amount |
| Eat_In_Or_Take_Away | text | Order type |
| Product Type | text | Product type |

**4. Git Repository Setup**
- ✅ Private GitHub repository created: `alikhanclear/casualhero-bi`
- ✅ `.gitignore` protecting credentials
- ✅ Initial commit pushed
- ✅ All foundational code in version control

**5. Sample Data Export**
- ✅ Exported 100 rows from `mv_item_details` to CSV
- ✅ Verified data structure and column names
- ✅ Confirmed drilldown and export requirements

### ✅ COMPLETED (Session 3 - Nov 5, 2025)

**1. Hosting Platform Decision**
- ✅ Evaluated 5 hosting options (Streamlit Cloud, Fly.io, Railway, Render, Digital Ocean)
- ✅ Analyzed RAM requirements for drilldown + export features
- ✅ **DECISION: Fly.io with 4GB RAM, always-on** (~£20-25/month)
- ✅ Documented rationale in Key Decisions section
- ✅ Phase 3 total cost estimate: ~£35/month (within budget)

**2. Power BI Dashboard Analysis**
- ✅ Analyzed Weekly Report.pdf (12 pages)
- ✅ Identified branding: Pink/pastel theme with Snowflake logo
- ✅ Documented Page 2 structure: YoY comparison matrix with 4 metric sections
- ✅ Identified interactive requirements: drill-down, data bars, conditional formatting
- ✅ **GOAL: Build "better than Power BI" with enhanced interactivity**

**3. Dashboard Requirements Identified**

**Page 2 - Weekly Report Table:**
- Multi-level grouping: Company → Establishment → Metrics
- 4 metric sections: Weekly Sales, 4W Avg, Order Volumes, ATV
- YoY comparisons with variance percentages
- Conditional formatting: RED/GREEN data bars
- Currency formatting, percentage formatting
- Hierarchical totals and subtotals

**Interactive Enhancements Beyond Power BI:**
- Click-to-expand drill-down (Company → Establishment → Daily → Transactions)
- Real-time filtering (week slider, company toggles, search)
- Smart insights panel (auto-detect patterns, alerts)
- Export filtered data at any drill level
- KPI cards with sparklines
- Animated transitions
- Mobile responsive
- Comparison mode (any two periods)
- Heatmap view option

### ✅ COMPLETED (Session 4 - Nov 8, 2025)

**1. KPI Calculator Module** (`src/core/kpi_calculator.py`)
- ✅ Complete KPI calculation engine built (690 lines)
- ✅ Weekly Sales calculations (Current Year, Last Year, YoY variance)
- ✅ 4-Week Average calculations with rolling window logic
- ✅ Order Volume calculations (unique order count, not line items)
- ✅ ATV (Average Transaction Value) calculations
- ✅ Company mapping (SNOWFLAKE, STRT SND, SKYVIEW)
- ✅ Hierarchical aggregation (Establishment → Company → Grand Total)
- ✅ Data preparation pipeline with fiscal calendar integration
- ✅ Production-ready: type hints, docstrings, error handling

**2. Infrastructure Decisions**
- ✅ Upgraded to 8GB RAM on Fly.io (from 4GB)
- ✅ Phase 3 cost target ACHIEVED: £30/month (Neon + Fly.io)
- ✅ RAM options evaluated (8GB/16GB/32GB)

**3. Weekly Report Analysis**
- ✅ Analyzed Power BI Weekly Report PDF (12 pages)
- ✅ Identified core report structure (Page 2: YoY comparison matrix)
- ✅ Mapped metrics: Weekly Sales, 4W Avg, Order Volumes, ATV
- ✅ Documented conditional formatting requirements (RED/GREEN bars)

**4. Reverse-Engineered Calculations**
- ⚠️ Built KPI calculations based on standard BI logic (NOT DAX yet)
- ⚠️ Assumptions made about aggregation logic
- ⚠️ NEEDS VALIDATION against actual Power BI DAX measures

### 🔄 IN PROGRESS

**Next Steps:**
1. **CRITICAL**: Get DAX measure examples from Power BI for validation
2. Test KPI calculator with sample data
3. Validate calculations against Power BI report outputs
4. Build Streamlit UI for Weekly Report page
5. Add conditional formatting (RED/GREEN bars)
6. Implement drill-down functionality

### ⏳ NEXT STEPS - Phase 1B: Build KPI Calculator

**Prerequisites from Client:**
1. **DAX Measure Examples (3-5 measures)**
   - YTD calculations
   - YoY comparisons
   - Budget variance formulas
   - Any time intelligence functions
   - Export from Power BI → Model → Manage measures

2. **Power BI Dashboard Screenshots**
   - Weekly report (5 pages) - annotated with what each chart shows
   - Monthly report (5-6 pages) - annotated with data sources
   - Matrix/table layouts with column names visible

**Development Tasks:**
1. Create `src/core/kpi_calculator.py`
2. Translate DAX measures to Polars/DuckDB expressions
3. Build test cases comparing against Power BI outputs
4. Validate all calculations match exactly

### ⏳ FUTURE PHASES

**Phase 1C: Build Streamlit Dashboard**
1. Create `src/ui/app.py` (main Streamlit app)
2. Implement weekly report (5 pages)
3. Implement monthly report (5-6 pages)
4. Deploy to Fly.io

**Phase 1D: MVP Delivery (Target: 2-3 weeks total)**
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

5. **Fly.io for Deployment (8GB RAM, Always-On)**
   - Chosen over Streamlit Community Cloud for drilldown + export capabilities
   - 8GB RAM handles large exports and transaction-level drilldowns with headroom
   - London region (lhr) for low latency to AWS RDS
   - Always-on configuration (no auto-sleep)
   - Cost: ~£20/month for 8GB VM
   - Phase 3 total: ~£30/month (Fly.io + Neon) - MEETS IDEAL TARGET!

   **RAM Options Evaluated:**
   - 8GB: £20/month (chosen - hits £30 target in Phase 3)
   - 16GB: £40/month (overkill for current needs)
   - 32GB: £80/month (at budget limit)

   **Why Fly.io over Streamlit Cloud:**
   - ✅ 8GB RAM vs 2GB (no export size limits needed)
   - ✅ UK-based hosting (lower latency to databases)
   - ✅ Full control over resources and scaling
   - ✅ Docker-based (better for complex deployments)
   - ⚠️ Requires Docker configuration (more complex than Streamlit Cloud)

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

**Last Updated:** Nov 8, 2025 - Session 4
**Next Session:** Validate KPI calculations with DAX measures, build Streamlit Weekly Report UI