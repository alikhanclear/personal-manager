# Personal Finance Manager - Project Context

## Project Overview
A personal finance management tool for importing and categorizing bank transactions using AI and rule-based categorization.

- **Bank**: NatWest (CSV import)
- **AI Provider**: Anthropic Claude Haiku (with prompt caching for 90% cost reduction)
- **Database**: SQLite (local storage)
- **UI Framework**: Dash (Plotly) with Bootstrap components
- **Language**: Python 3.11+

---

## 🔴 RULES OF ENGAGEMENT (Communication Protocol)

**CRITICAL: Always Be Verbose About Changes**

### 1. Before Any Destructive Operation
- ✅ **Explain WHAT** will be deleted/modified/overwritten
- ✅ **Explain the IMPACT** (what the user will lose)
- ✅ **Ask for PERMISSION** before proceeding
- ✅ **Offer alternatives** (backup, preserve data, different approach)

**Example:**
```
"I'm about to run a script that will:
1. DELETE ALL 83 rules from your database (including custom rules)
2. Recreate only 62 default rules
3. Your custom 'VIZARAT ALIKHAN → Healthcare' rule will be LOST

Do you want me to:
- A) Proceed (you'll recreate custom rules later)
- B) Write a smarter script that preserves custom rules
- C) Backup the database first"
```

### 2. During Implementation
- ✅ Explain each step as you work
- ✅ Show what's changing and why
- ✅ Use TodoWrite to track progress
- ✅ Don't assume the user knows what you're doing

### 3. After Each Activity - ALWAYS Summarize
- ✅ **What was changed** (which files, what code)
- ✅ **What data was affected** (database changes, deletions)
- ✅ **What the user needs to test/verify**
- ✅ **Highlight any data loss or breaking changes**
- ✅ **Document in session notes at the end**

### 4. Learning Together
- ✅ Explain the "why" behind decisions
- ✅ Show the complete flow/logic
- ✅ Help user understand the system, not just fix bugs
- ✅ User should be able to make informed decisions

### Examples:
- ❌ **BAD**: "Let me run this fix script" → runs it → "Done!"
- ✅ **GOOD**: "This script will delete X, modify Y, and impact Z. The trade-off is... Do you want me to proceed or explore alternatives?"

---

## Tech Stack
- **Frontend**: Dash + dash-bootstrap-components + dash-table
- **Data Processing**: Polars (CSV parsing), Pandas (display)
- **Database**: SQLite with Pydantic models
- **AI**: Anthropic Claude Haiku (`claude-3-haiku-20240307`)
- **Background Processing**: subprocess.Popen for long-running AI tasks

## Core Features

### 1. Transaction Import
- Upload NatWest CSV files (auto-detects delimiter: comma or semicolon)
- Deterministic transaction IDs (MD5 hash) for duplicate detection
- Automatic duplicate prevention on re-upload
- Parses: Date, Description, Amount, Balance, Account Number

### 2. Categorization System

**Two-Tier Approach:**
1. **Rule-Based (Free, Instant)**
   - Pattern matching on transaction descriptions
   - Priority-based rule ordering
   - Confidence = 1.0 for rule matches

2. **AI Fallback (Paid, Slower)**
   - Claude Haiku with prompt caching (90% cost reduction)
   - Rate-limited to 42 requests/min (under 50/min API limit)
   - Confidence = 0.0-0.99 for AI suggestions
   - Retry logic with exponential backoff
   - Background processing with live progress tracking

**Confidence Values:**
- `1.0` = Rule matched or manually confirmed
- `0.0-0.99` = AI suggestion (needs review)
- `None` = Uncategorized

### 3. Background AI Processing
- Launched via subprocess (detached from UI)
- Live progress tracking via JSON file (polled every 3 seconds)
- Displays: processed count, rule matched, AI categorized, ETA
- Stall detection (warns if no update for 5+ minutes)
- 1.4 second delay between AI requests (rate limiting)

### 4. Review & Correction Workflow
- Filter views:
  - Rule Matched (auto-categorized)
  - AI Suggestions (needs review)
  - Uncategorized Only
  - Confirmed
  - All Transactions
- Inline category editing
- **Confirm** button: Mark category as correct (confidence = 1.0)
- **Confirm & Create Rule** button: Confirm + create pattern-based rule for future

### 5. Rules Management
- Dedicated "Rules" tab showing ALL rules (no pagination)
- Scrollable list with sticky header
- Sortable and filterable
- Auto-refreshes every 10 seconds
- Shows: Pattern, Category, Priority, Created Date

### 6. Statistics Dashboard
- Total transactions
- Total categories
- Active rules count

## Data Model

### Transaction
```python
id: str                    # MD5 hash(date|description|amount|account)
date: datetime
description: str
amount: float
balance: float
account_number: str
category: Optional[str]
category_confidence: Optional[float]
category_confirmed: bool   # True if user confirmed
```

### Category
```python
id: str
name: str
description: str
parent_id: Optional[str]   # For hierarchical categories
```

### Rule
```python
pattern: str               # Regex pattern to match description
category_id: str
priority: int              # Higher priority = checked first
```

## Project Structure
```
personal-finance/
├── app.py                          # Main Dash application
├── run_ai_categorization.py        # Background AI script
├── src/
│   ├── data/
│   │   ├── database.py             # SQLite connection + queries
│   │   ├── models.py               # Pydantic models
│   │   └── parser.py               # NatWest CSV parser
│   ├── core/
│   │   ├── categorizer.py          # Hybrid categorization engine
│   │   ├── rule_matcher.py         # Pattern matching logic
│   │   └── progress_tracker.py     # Background progress tracking
│   ├── ml/
│   │   └── ai_categorizer.py       # Claude AI integration
│   └── utils/
│       └── categories.py           # Default category setup
├── scripts/
│   ├── init_database.py            # Initialize fresh database
│   ├── fix_confidence_values.py    # Fix existing data (one-time)
│   └── debug_rule_filter.py        # Debug filtering issues
├── data/
│   ├── finance.db                  # SQLite database
│   └── ai_progress.json            # Progress tracking file
├── .env                            # APP_ANTHROPIC_API_KEY (gitignored)
└── requirements.txt
```

## Current Status

### ✅ COMPLETED (Latest Session)

**UI/UX Improvements:**
- Fixed "Confirm" button (now includes confidence=1.0)
- Fixed "Confirm & Create Rule" button (now includes confidence=1.0)
- Moved Rules from collapsible section to dedicated tab
- Rules tab shows ALL rules without pagination (scrollable)
- Sticky table headers for better navigation

**Workflow:**
1. 📥 Import & Categorize Tab:
   - Step 1: Upload CSV
   - Step 2: Apply Rules (batch, instant)
   - Step 3: Start AI Categorization (background with live progress)

2. 📋 Review & Correct Tab:
   - Filter transactions by status
   - Edit categories inline
   - Confirm or Confirm + Create Rule

3. 📊 Statistics Tab:
   - Transaction counts and category stats

4. 📝 Rules Tab:
   - View all rules in one scrollable list
   - Sort and filter
   - Auto-refresh

### ✅ RESOLVED ISSUES

1. **Claude AI Model 404** - Fixed model name to `claude-3-haiku-20240307`
2. **Rate Limit 429** - Added 1.4s delay between requests (42/min)
3. **Confidence Values Not Saved** - Fixed database update calls
4. **Duplicate Transactions** - Implemented deterministic MD5 IDs
5. **Process Stuck at 350 Records** - Added retry logic and stall detection
6. **Confirm Buttons Not Working** - Fixed missing confidence parameter
7. **Rules Display** - Moved to separate tab, removed pagination

## Default Categories

### Income
- Salary
- Freelance Income
- Investment Returns
- Other Income

### Fixed Expenses
- Rent/Mortgage
- Utilities
- Insurance
- Subscriptions

### Variable Expenses
- Groceries
- Dining Out
- Transportation
- Entertainment
- Shopping
- Healthcare
- Personal Care

### Savings & Investments
- Savings Transfer
- Investment Contributions

### Debt
- Loan Payments
- Credit Card Payments

### Uncategorized
- Default for unknown transactions

## Key Technical Decisions

1. **Deterministic Transaction IDs**
   - MD5 hash of (date|description|amount|account)
   - Prevents duplicate imports automatically
   - Same transaction = same ID = `INSERT OR IGNORE`

2. **Background AI Processing**
   - Avoids blocking UI during long AI runs
   - subprocess.Popen with detached process
   - JSON file polling for progress updates
   - User can continue using app while AI runs

3. **Confidence-Based Filtering**
   - `confidence = 1.0` for trusted (rules/confirmed)
   - `confidence < 1.0` for AI suggestions (needs review)
   - `confidence = None` for uncategorized
   - Enables smart filtering in review tab

4. **Rate Limiting Strategy**
   - 1.4 second delay between AI requests
   - Target: 42 requests/min (safely under 50/min limit)
   - Retry logic: exponential backoff for failures
   - Timeout: 30 seconds per request

5. **Prompt Caching**
   - System prompt includes all categories (cached)
   - 90% cost reduction on repeated requests
   - Cache valid for 5 minutes
   - Massive savings for batch processing

## Environment Setup

### Required Environment Variables
```bash
APP_ANTHROPIC_API_KEY=sk-ant-...    # Get from console.anthropic.com
```

### Installation
```bash
cd personal-finance
pip install -r requirements.txt
python scripts/init_database.py  # First time only
python app.py                    # Run the app
```

## Future Features (Roadmap)

### 🔮 Planned Features

1. **Budget Tracking**
   - Set monthly/weekly budgets per category
   - Track spending against budget
   - Alerts when approaching budget limits
   - Budget vs. Actual reports
   - Rollover unused budget to next period

2. **Weekly Transaction Reports**
   - Generate formatted weekly summaries
   - Copy-paste friendly format for emails
   - Include: spending by category, notable transactions, budget status
   - Export options: Plain text, Markdown, HTML
   - Scheduled email reports (optional)

3. **Future Enhancements (TBD)**
   - Multi-bank support (beyond NatWest)
   - Recurring transaction detection
   - Trend analysis and forecasting
   - Custom category hierarchies
   - Rule suggestions based on manual categorizations
   - Export to CSV/Excel
   - Mobile-friendly responsive design
   - Multi-user support with authentication

## Development Notes

### Running the Application
```bash
# Start the Dash server
python app.py

# Access at: http://localhost:8050/
```

### Database Management
```bash
# Initialize fresh database
python scripts/init_database.py

# Fix confidence values (one-time migration)
python scripts/fix_confidence_values.py

# Debug filtering issues
python scripts/debug_rule_filter.py
```

### Manual Rule Creation
Rules are created automatically when you click "Confirm & Create Rule" in the Review tab. The system suggests a pattern based on the transaction description.

## Git Workflow

**Current Branch**: `claude/personal-finance-01VjZZFozL9KrFhnUkEB8B2u`

### Recent Commits
- Fix confirm buttons and move Rules to separate tab
- Add retry logic and stall detection for AI categorization
- Add deterministic transaction IDs for duplicate detection
- Add background AI categorization with live progress tracking
- Improve progress tracking and recommend terminal for AI

## Cost Optimization

### AI Categorization Costs
- **Without Prompt Caching**: ~$0.0005 per transaction
- **With Prompt Caching**: ~$0.00005 per transaction (90% reduction)
- **Estimated Monthly Cost** (1000 new transactions): ~$0.05/month

### Best Practices
1. Always run Rule-Based categorization first (free)
2. Only use AI for uncategorized transactions
3. Create rules from confirmed transactions to reduce future AI usage
4. Use batch processing (background mode) for large imports

## Troubleshooting

### Issue: Transactions not appearing after upload
- Check upload status message for errors
- Verify database file exists in `data/finance.db`
- Check browser console for errors
- Try refreshing the page

### Issue: AI categorization stuck
- Check `data/ai_progress.json` for status
- Look for "stall detected" warning in UI
- Check API key is valid in `.env`
- Check internet connection
- Review terminal output for errors

### Issue: Duplicate transactions
- Should be prevented automatically via MD5 IDs
- If seeing duplicates, check if any fields changed (amount, date, etc.)
- Delete `data/finance.db` and start fresh if needed

### Issue: Confirm buttons not working
- **FIXED** in latest commit
- Ensure you've pulled latest code
- Check confidence values are being saved

---

**Last Updated**: November 23, 2025
**Current Session**: Rule engine rewrite + token-based matching
**Current Branch**: `personal-finance/dash-no-aggrid`

## ✅ Completed Sessions

### Session: Nov 23, 2025 - Rule Engine Rewrite

**Major Changes:**

1. **Removed All Auto-Refresh Behavior**
   - Review & Correct tab no longer auto-refreshes after category changes
   - User has complete manual control via "Refresh" button
   - Added success messages: "✓ Category changed to 'X'. Click 'Refresh' to see changes."
   - **Files**: `app.py` (callbacks: `save_review_category_change`, `batch_confirm`, etc.)

2. **Rewrote Rule Matching Engine (Whole-Word Token Matching)**
   - **Problem**: Pattern "TFL" was matching "NETFLIX" (substring match)
   - **Solution**: Token-based matching using `re.split(r'[\s,*\-./\\|()]+', ...)`
   - Pattern must match complete tokens, not substrings
   - Examples:
     - "NETFLIX" matches "PAYPAL *NETFLIX" ✓
     - "TFL" does NOT match "NETFLIX" ✗
     - "TFL" matches "TFL TRAVEL" ✓
   - **Files**: `src/core/rule_engine.py` (complete rewrite of `_matches_pattern()`)

3. **Added "Force Re-categorize" Feature**
   - New checkbox in Rules tab
   - **Default OFF**: Protects confirmed transactions
   - **Enabled**: Re-categorizes ALL transactions including confirmed ones
   - Use case: Fix mistakes, apply new rules to everything
   - **Files**: `app.py` (UI + callback), `src/core/categorizer.py` (`force_recategorize` parameter)

4. **Implemented Bulk Rule Deletion**
   - Added checkboxes to Rules table (`row_selectable='multi'`)
   - New button: "🗑️ Delete Selected Rules"
   - Deletes rules permanently from database
   - **Files**: `app.py` (callback: `delete_selected_rules`)

5. **Added "Add New Rule" Feature**
   - New button: "➕ Add New Rule"
   - Modal dialog with form: Pattern, Category dropdown, Priority
   - **Files**: `app.py` (modal UI + callbacks: `toggle_add_rule_modal`, `save_new_rule`)

6. **Aligned All Buttons in Rules Tab**
   - Used `dbc.ButtonGroup` for clean layout
   - Buttons: Add New Rule, Refresh, Delete Selected, Re-categorize ALL, Export to Excel
   - **Files**: `app.py` (line ~496-508)

7. **Fixed Broken Netflix Rule**
   - **Problem**: category_id stored as "Streaming Services" (name) instead of UUID
   - **Fix**: Updated database to use proper UUID
   - Created debug scripts: `check_all_rules.py`, `fix_netflix_quick.py`
   - **Result**: All 12 Netflix transactions now correctly categorized

8. **Fixed `case_insensitive_value` Error**
   - Removed reference to deleted UI component
   - Hardcoded default: case-insensitive filtering
   - **Files**: `app.py` (line 950, line 999)

**Key Lesson Learned:**
- ✅ **Categorization should be driven from Rules tab with force re-categorize**
- ❌ Doing it transaction-by-transaction in Review & Correct tab is inefficient
- **Best workflow**: Fix rules → Force re-categorize ALL → Review outliers

**Debug Scripts Created:**
- `scripts/debug_netflix.py` - Check Netflix transactions
- `scripts/debug_all_rules.py` - Show all rules and test matching
- `scripts/test_token_matching.py` - Test whole-word matching (13/13 tests passed)
- `scripts/check_all_rules.py` - Check for broken category_ids
- `scripts/fix_netflix_quick.py` - Fix broken Netflix rule

---

### Session: Nov 22, 2025 - Duplicate Detection System

**Completed:**

1. **Fixed "Re-categorize ALL with Rules" Button**
   - **OLD**: Overwrote ALL categorizations including AI suggestions
   - **NEW**: Only processes uncategorized + rule-matched transactions
   - **Preserves**: AI suggestions (confidence<1.0) and user confirmations

2. **Added "Purge All Transactions" Feature**
   - New button in Rules tab with confirmation modal
   - Deletes ALL transactions, preserves rules and categories
   - Use case: Start fresh with new CSV while keeping learned rules

3. **Implemented Duplicate Detection & Review System**
   - **Problem Solved**: MD5 hash-based IDs were silently skipping duplicates
   - Same transaction twice in one day (e.g., 2 coffees) was being lost
   - **New System**:
     - Database table: `potential_duplicates`
     - New tab: "🔍 Review Duplicates"
     - Upload message shows: "⚠️ Potential duplicates: X"
     - User actions: "Keep Both" or "Dismiss"
   - **Files Changed**:
     - `src/data/models.py` - Added PotentialDuplicate model
     - `src/data/database.py` - Added duplicates table + methods
     - `app.py` - New tab + callbacks for duplicate review

---

## 🔴 PRIORITY FOR NEXT SESSION (Nov 24, 2025)

### Excel/CSV Import for Rules (Bulk Rule Management)

**Problem**:
- Currently, rules can only be added one-by-one via UI modal
- No way to bulk upload or manage large rule sets
- Difficult to maintain rules in version control or share with others

**Solution**: Add Excel/CSV import functionality in Rules tab

**Two Import Modes:**

1. **Mode 1: Overwrite All Rules (Replace)**
   - Deletes ALL existing rules from database
   - Imports new rules from CSV/Excel file
   - Use case: Complete rule set replacement, reset to clean state
   - **Warning required**: "This will DELETE all X existing rules. Continue?"

2. **Mode 2: Incremental/Batch Add (Append)**
   - Keeps existing rules in database
   - Adds new rules from CSV/Excel file
   - Handles duplicates: Skip if pattern + category already exists
   - Use case: Adding new rules without losing existing ones

**CSV/Excel Format:**
```csv
pattern,category,priority
NETFLIX,Streaming Services,10
TFL,Public Transport,10
TESCO,Groceries,10
AMAZON,Shopping,5
```

**Implementation Notes:**
- Add "📥 Import Rules" button in Rules tab ButtonGroup
- Modal dialog with:
  - File upload (CSV or Excel)
  - Radio buttons: "Replace All Rules" or "Add New Rules"
  - Preview table showing parsed rules
  - Validation: Check category names exist, valid priority values
- Use Polars to parse CSV/Excel (fast, robust)
- Map category names to UUIDs before insert
- Show summary: "✓ Imported X rules (Y skipped as duplicates)"

**Files to Modify:**
- `app.py` - Add upload UI, callbacks for import
- `src/data/database.py` - Add `import_rules()` and `replace_all_rules()` methods

**Benefits:**
- Backup/restore rule sets easily
- Share rules across environments (dev/prod)
- Version control rules in Git (CSV file)
- Bulk edit in Excel, re-import
- Faster onboarding (import pre-configured rules)

---

## 📋 Future Enhancements (Backlog)

### Batch Operations in Review & Correct Tab
- Add checkbox column to transactions table
- Batch actions: "Confirm Selected", "Confirm & Create Rules Selected"
- UX: Similar to email clients (Gmail/Outlook style)

### Rule Conflict Detection & Resolution
- Detect when multiple rules match the same transaction
- Show warnings when rules overlap (non-blocking)
- Rule priority strictly enforced (first match wins)

### Other Priorities
- Budget tracking and weekly reports implementation
- Performance optimization for large datasets
- Export enhancements

---

## 🚨 NEXT SESSION - START HERE FIRST! 🚨

**Date**: November 25, 2025
**CRITICAL PRIORITY**: Regression Testing & Progress Window Completion

### ⚠️ MUST DO BEFORE ANY NEW WORK:
**The user does NOT want to break existing functionality. Regression testing is CRITICAL.**

### Session Goals:
1. **REGRESSION TEST EVERYTHING** (highest priority)
   - Test transaction upload (CSV import)
   - Test transaction type categorization (INT/CHG → Interest and Charges)
   - Test rule matching
   - Test AI categorization (verify it doesn't overwrite rule-matched transactions)
   - Test Excel export with Status column
   - Test manual categorization in Review & Correct tab
   - Test rule import/export
   - Verify all existing features work as before

2. **Complete Progress Window Implementation** (only after regression tests pass)
   - Add callbacks to show/hide progress modal
   - Wire up progress polling with dcc.Interval
   - Connect progress tracker to UI updates
   - Test progress window during AI categorization

### Work Already Completed (Nov 25, 2025):
✅ **Transaction Type Categorization**
- Added INT/CHG → "Interest and Charges" categorization
- This is now the HIGHEST priority (Step 0, before rules)
- Files: `src/core/categorizer.py`

✅ **AI Protection**
- Dual-layer protection to prevent AI from overwriting rule-matched transactions
- Filter in `app.py` (line 910-915)
- Skip logic in `categorizer.py` (line 186-194)

✅ **Excel Export Enhancement**
- Added "Status" column showing: Confirmed, Rule Matched, AI Suggested, Uncategorized
- File: `app.py` (export function)

✅ **Progress Window Infrastructure (90% complete)**
- `src/utils/progress_tracker.py` - JSON-based progress tracking
- Progress modal UI in `app.py` (lines 702-734)
- `dcc.Interval` component for polling
- Progress updates in `categorizer.py`
- **REMAINING**: Callbacks to wire it all together

### Files Modified in This Session:
1. `app.py` - Added Status column to export, AI protection filter, progress modal UI
2. `src/core/categorizer.py` - Transaction type check, AI protection, progress tracking
3. `src/utils/progress_tracker.py` - NEW FILE (progress tracking system)
4. `scripts/add_interest_charges_category.py` - NEW FILE (utility)

### Testing Checklist for Next Session:
- [ ] Upload test CSV file
- [ ] Verify INT/CHG transactions auto-categorize
- [ ] Apply rules - verify they work
- [ ] Run AI categorization - verify it doesn't overwrite rules
- [ ] Export to Excel - verify Status column exists
- [ ] Manually edit categories in Review & Correct
- [ ] Test all tabs work without errors

**REMEMBER**: User priority is stability over new features. Test thoroughly!

---

## 🚨 Session: Nov 29, 2025 - Regression Testing Infrastructure

**Status**: Regression testing **DEFERRED** but infrastructure ready

**What Was Built:**
- ✅ Test database creation script: `scripts/init_test_database.py`
- ✅ Data copy script: `scripts/copy_categories_rules_to_test.py`
- ✅ Fresh test database: `data/finance_test.db` (67 categories, 120 rules)
- ✅ Comprehensive test CSV: `regression_test.csv` (20 transactions with INT/CHG types)
- ✅ Documented testing procedure

**How to Run Regression Tests (When Ready):**
1. `python scripts/init_test_database.py` - Create fresh test DB
2. `python scripts/copy_categories_rules_to_test.py` - Copy categories/rules
3. Modify `app.py` line 40: `finance.db` → `finance_test.db`
4. Run tests with `regression_test.csv`
5. Restore `app.py` to use `finance.db`

**Test Coverage Needed:**
- [ ] CSV upload functionality
- [ ] INT/CHG auto-categorization
- [ ] Rule-based matching (token-based)
- [ ] AI categorization doesn't overwrite rules
- [ ] Excel export with Status column
- [ ] Manual categorization in Review & Correct
- [ ] All tabs load without errors

**Decision**: User wants to **complete the build first**, regression testing later.

---

**Git Repository**: Private repo `personal-finance-fresh`
**Database**: `data/finance.db` (SQLite)
**Server**: http://localhost:8050/
