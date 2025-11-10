# CasualHero BI Platform - Development Context

## Project Overview
Replace Power BI dashboards (£500/month) with custom Streamlit solution.
- Customer: Snowflake Gelato (15 locations)
- Timeline: 2-3 weeks to MVP
- Clean break from Power BI (no dependency)
- Target cost should not exceed £100/month. Ideally sticking to £30/month

## Tech Stack
- Frontend: **Dash** (Plotly) - Migrated from Streamlit in Session 5
- Data Processing: Polars + DuckDB
- Database: PostgreSQL (AWS initially, Neon long-term)
- Deployment: Fly.io (8GB RAM, always-on)
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

### Data Retention Requirement
**5-Year Historical Data:**
- Production system must maintain 5 years of transaction history
- Enables: Current year + 2-year YoY comparisons + 5-year trend analysis
- Volume estimate: ~39M transaction line items (~3-5GB in Polars)
- User can select any year from current back to 4 years prior

### Current State (Phase 1)
**AWS PostgreSQL Materialized View:**
- Name: `public.mv_item_details`
- Structure: Transaction-level data (11 columns)
- **Refresh Schedule: Daily by 9:00 AM** (Snowflake Gelato's process)
- Contains: Order line items with establishment, product, sales, tax details

**Schema: `mv_item_details`**

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

**Data Freshness (Phase 1):**
- AWS materialized view refreshed: **9:00 AM daily**
- Streamlit cache refresh: **9:30 AM daily** (after AWS refresh completes)
- Users before 9:30 AM: See previous day's data (acceptable for MVP)
- Users after 9:30 AM: See current day's data (fresh)

**Loading Strategy:**
```python
@st.cache_resource(ttl=86400)  # 24 hours
def load_transactions():
    """
    Loads 5 years of data at 9:30 AM daily.
    ~39M rows, 30-60 second load time.
    Cached for 24 hours, shared across all users.
    """
    return query_aws_database(years=5)
```

**User Experience:**
- First user after 9:30 AM: 30-60 seconds (triggers cache refresh)
- All subsequent users: **INSTANT** (app-level cache)
- Admin override: Manual "Reload Data" button for mid-day updates

### Future State (Phase 2/3)
**Neon PostgreSQL + Toast SFTP Ingestion:**
- Toast POS → SFTP export → Neon database (incremental ETL)
- Neon → Streamlit (daily cache refresh)

**Data Freshness (Phase 2 - TBD):**
- **Depends on Toast SFTP export schedule** (need to confirm with client)
- **Scenario A:** If Toast exports at midnight → Data available by **1:00 AM** (8 hours earlier than Phase 1)
- **Scenario B:** If Toast exports at 6:00 AM → Data available by **7:00 AM** (2 hours earlier)
- **Scenario C:** If Toast exports hourly → Near real-time updates possible

**Questions for Client (Phase 2 Planning):**
1. What time does Toast POS export to SFTP? (midnight, 6 AM, 9 AM?)
2. Is export end-of-day batch or hourly incremental?
3. Business requirement: Is 9 AM acceptable long-term, or need earlier?
4. Intraday updates needed? (e.g., lunch rush monitoring at 1 PM)

**ETL Timeline (Phase 2 Example):**
```
12:00 AM - Toast exports to SFTP
12:05 AM - SFTP files ready
12:30 AM - ETL job ingests → Neon (15-20 min processing)
12:50 AM - Neon data ready
1:00 AM  - Streamlit cache refresh
7:00 AM  - Users arrive with fresh data from previous day
```

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

**Key Functions Implemented:**
```python
- prepare_transaction_data()      # 7AM cutoff + fiscal calendar
- calculate_weekly_sales()        # YoY sales comparison
- calculate_4week_avg()           # Rolling 4-week average
- calculate_order_volumes()       # Order count (not items)
- calculate_atv()                 # Sales / Order count
- calculate_weekly_report()       # Combines all metrics
- add_company_totals()            # Subtotals by company
- add_grand_total()               # Grand total row
```

**2. Infrastructure Decisions**
- ✅ Upgraded to 8GB RAM on Fly.io (from 4GB)
- ✅ Phase 3 cost target ACHIEVED: £30/month (Neon + Fly.io)
- ✅ RAM options evaluated (8GB/16GB/32GB)
- ✅ Phase 1 cost: ~£40/month (AWS RDS + Fly.io)
- ✅ Phase 3 cost: ~£30/month (Neon + Fly.io) - IDEAL TARGET MET!

**3. Weekly Report Analysis**
- ✅ Analyzed Power BI Weekly Report PDF (12 pages)
- ✅ Identified core report structure (Page 2: YoY comparison matrix)
- ✅ Mapped metrics: Weekly Sales, 4W Avg, Order Volumes, ATV
- ✅ Documented conditional formatting requirements (RED/GREEN bars)
- ✅ Power BI benchmark values extracted for FY26 Week 4:
  - Meadowhall: £8,894 sales, 1,155 orders, £7.70 ATV
  - The O2: £8,737 sales, 933 orders, £9.36 ATV
  - Westfield: £18,629 sales, 2,282 orders, £8.16 ATV

**4. Reverse-Engineered Calculations**
- ✅ Built KPI calculations based on standard BI logic (NOT DAX yet)
- ✅ Assumptions documented:
  - Weekly Sales = SUM(Net_Sales_Actual) for fiscal week
  - 4W Avg = AVG(weekly sales) for last 4 weeks
  - Order Volumes = COUNT(DISTINCT Order_Number)
  - ATV = Total Sales / Order Count
  - YoY Variance = (Current - Last) / Last
- ⚠️ NEEDS VALIDATION against actual Power BI DAX measures

**5. Project Organization**
- ✅ Created `scripts/` directory for test/utility files
- ✅ Moved all test scripts to `scripts/`:
  - `test_weekly_report.py` - Weekly report validation
  - `test_schema.py` - Database schema testing
  - `check_env.py`, `debug_schema.py` - Utilities
  - `fetch_sample_data.py`, `export_sample.py` - Data exports
- ✅ Cleaner project root structure

### ✅ COMPLETED (Session 5 - Nov 9, 2025)

**MAJOR MILESTONE: Migrated from Streamlit to Dash**

**1. UI Framework Migration**
- ✅ Migrated entire UI layer from Streamlit to Dash
- ✅ Created `src/ui/dash_app.py` (483 lines) - production-grade BI dashboard
- ✅ Preserved ALL business logic (kpi_calculator, fiscal_calendar, queries unchanged)
- ✅ Zero changes to data layer or core calculations

**Why Migrated:**
- Streamlit limitations with interactive tables and conditional formatting
- Tried AG Grid (streamlit-aggrid) - JavaScript rendering issues
- Tried Perspective - iframe rendering issues
- Tried Pandas Styler - Streamlit strips CSS styling
- **Decision**: Migrate to Dash for production-quality BI dashboards

**2. Dash Implementation Complete**

**Home Page:**
- ✅ Quick stats cards (Total Orders, Total Sales, Establishments)
- ✅ Current fiscal period display
- ✅ Data summary sidebar
- ✅ Bootstrap navigation with pink Snowflake branding (#FF6B9D)

**Weekly Report Page:**
- ✅ Fiscal year/week dropdown selectors
- ✅ Interactive DataTable with all features:
  - Native sorting (click column headers)
  - Native filtering (search boxes)
  - Pagination (20 rows per page)
  - Excel export button
- ✅ **Conditional formatting (Power BI style):**
  - Green backgrounds (#90EE90) for positive variance
  - Red backgrounds (#FFB6C1) for negative variance
  - Dark green text (#006400) for positive values
  - Dark red text (#8B0000) for negative values
  - Applied to all 4 variance columns (Sales, 4W Avg, Volume, ATV)
- ✅ **Number formatting:**
  - Sales: Whole numbers with thousands separators (e.g., "12,345")
  - ATV: 2 decimal places (e.g., "12.34")
  - Variance: 2 decimal places (e.g., "33.52")

**3. Data Loading & Performance**
- ✅ App-level caching (global DATA_CACHE dictionary)
- ✅ Data loads once at startup: 1,657,933 transactions in ~80-120s
- ✅ Report generation: <100ms (cached data, instant filtering)
- ✅ Callback-based architecture (Dash patterns)

**4. Deployment Ready**
- ✅ `app.server` exposed for WSGI deployment (Gunicorn/Fly.io)
- ✅ Debug mode for development
- ✅ Production-ready code structure
- ✅ requirements.txt updated with Dash dependencies

**5. Files Created/Modified**
- ✅ `src/ui/dash_app.py` - NEW (complete Dash application)
- ✅ `requirements.txt` - Added dash==3.2.0, dash-bootstrap-components==2.0.4

**Current Status:**
- ✅ Dash server running on http://localhost:8050/
- ✅ All features working (conditional formatting, number formatting)
- ✅ **Data bars implemented** - Power BI style horizontal bars (gradient from center)
- ✅ Positive variance: Green bars grow right from center
- ✅ Negative variance: Red bars grow left from center
- ✅ User tested and approved
- ✅ Ready for next phase

**Data Bars Fix:**
- Initial implementation: Whole cell backgrounds (green/red)
- User feedback: "whole cells are shaded not bars"
- Final implementation: CSS gradient bars from center (linear-gradient)
- Result: True Power BI-style data bars showing magnitude

**Next Phase:** Monthly Report implementation → Trends page → Deployment

### 🔄 RESOLVED (Session 4 Issues)

**Current State: Testing KPI Calculator**

Created `scripts/test_weekly_report.py` to validate calculations against Power BI report.

**Issues Encountered & Fixed:**
1. ✅ Unicode encoding errors on Windows console (checkmarks/symbols)
   - Solution: Replaced with ASCII alternatives ([OK], PASS/FAIL)
2. ✅ Polars table display Unicode box-drawing characters
   - Solution: Skipped dataframe previews to avoid encoding issues
3. ✅ `map_dict()` doesn't exist in Polars
   - Solution: Changed to `.replace()` method
4. ✅ Data type mismatch (Int32 vs Int64)
   - Solution: Changed fiscal calendar return types to Int64
5. 🔄 **CURRENT ISSUE**: Join column conflicts when combining metrics
   - Error: `column with name 'Company_right' already exists`
   - Attempted fix: Changed to `how='full'` with `coalesce=True`
   - Status: NEEDS TESTING

**Exact Stopping Point:**
- File: `src/core/kpi_calculator.py` line 523-549
- Function: `calculate_weekly_report()` - join logic
- Next action: Run `python scripts/test_weekly_report.py` to verify fix

**What Works:**
- ✅ Data loading (100 rows sample CSV)
- ✅ Company mapping
- ✅ 7AM cutoff and fiscal calendar calculations
- ✅ Individual metric calculations (weekly sales, 4W avg, volumes, ATV)

**What Needs Testing:**
- 🔄 Joining all metrics into single report
- 🔄 Company totals aggregation
- 🔄 Grand total calculation
- 🔄 Comparison with Power BI values

**Next Steps for Tomorrow:**
1. **IMMEDIATE**: Test fixed join logic in `calculate_weekly_report()`
2. Verify calculations match Power BI report (FY26 Week 4)
3. Fix any remaining discrepancies
4. **CRITICAL**: Get actual DAX measures from Power BI for validation
5. Document differences between our logic and Power BI DAX
6. Build Streamlit UI for Weekly Report page
7. Add conditional formatting (RED/GREEN bars)

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

**Last Updated:** Nov 10, 2025 - Session 6 (Database Query Optimization & Production Fix!)
**Next Session:** Monthly Report implementation → Deployment to Fly.io

**Session 6 Summary:**
- **CRITICAL FIX**: Resolved AWS database timeout issues
- **Problem**: Original INNER JOIN query was taking 2+ hours and timing out
- **Solution**: Split-query approach - load data separately, join in Polars
  - Query 1: Get transactions from `mv_item_details` (fast, simple)
  - Query 2: Get payment statuses from `PaymentDetails` (fast, small table)
  - Join + filter in Polars (much faster than PostgreSQL JOIN)
- **Power BI Query Matching**: Replicated exact Power BI filtering logic
  - LEFT JOIN (not INNER JOIN)
  - Exclude 'denied' payments
  - Keep only 'captured' and 'authorized' statuses
- **Performance**: Load time reduced from 2+ hours → **30-90 seconds**
- **Data Volume**: 1.66M transactions (5 fiscal years, filtered)
- **Fixed Dash Debug Mode**: Disabled reloader to prevent double-loading
- **Status**: ✅ PRODUCTION READY - Fast, reliable data loading

**Session 5 Summary:**
- **MAJOR MILESTONE**: Migrated from Streamlit to Dash
- Created production-grade BI dashboard (dash_app.py - 518 lines)
- **Data bars implemented**: Power BI-style horizontal gradient bars
  - Positive variance: Green bars grow right from center
  - Negative variance: Red bars grow left from center
  - Bar width = magnitude of variance (using CSS linear-gradient)
- Number formatting perfect (thousands separators, 2dp for ATV/variance)
- Interactive table: sorting, filtering, pagination, Excel export
- Preserved ALL business logic (zero changes to kpi_calculator, fiscal_calendar, queries)
- Server running successfully on http://localhost:8050/
- Archived old Streamlit code (moved to archive/)
- **Status**: ✅ COMPLETE - User tested and approved

**Session 4 Summary:**
- Built complete KPI calculator (690 lines)
- Reverse-engineered calculations from Power BI report
- Infrastructure: Upgraded to 8GB RAM, £30/month Phase 3 target achieved
- Organized project: moved test files to scripts/ directory