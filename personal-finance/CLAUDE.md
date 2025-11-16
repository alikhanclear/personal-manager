# Personal Finance Manager - Project Context

## Project Overview
A personal finance management tool for importing and categorizing bank transactions using AI and rule-based categorization.

- **Bank**: NatWest (CSV import)
- **AI Provider**: Anthropic Claude Haiku (with prompt caching for 90% cost reduction)
- **Database**: SQLite (local storage)
- **UI Framework**: Dash (Plotly) with Bootstrap components
- **Language**: Python 3.11+

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
├── .env                            # ANTHROPIC_API_KEY (gitignored)
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
ANTHROPIC_API_KEY=sk-ant-...    # Get from console.anthropic.com
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

**Last Updated**: November 16, 2025
**Current Session**: Fix confirm buttons and Rules tab workflow
**Next Steps**: Budget tracking and weekly reports implementation
