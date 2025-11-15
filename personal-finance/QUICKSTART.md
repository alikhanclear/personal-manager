# Personal Finance Manager - Quick Start

Get up and running in 5 minutes!

## Installation

### 1. Install Dependencies

```bash
# From the personal-finance directory
pip install -r requirements.txt
```

**Required packages:**
- `polars` - Fast data processing
- `pydantic` - Data validation
- `dash` - Web UI framework
- `dash-bootstrap-components` - UI components
- `anthropic` - Claude AI (optional, for AI categorization)

### 2. Set Up API Key (Optional - for AI categorization)

If you want AI categorization for transactions that don't match rules:

```bash
# Get API key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Without API key:** Rules-only mode (FREE, instant for known merchants)
**With API key:** Hybrid mode (rules + AI fallback for ~$0.10-0.50 per 1000 transactions)

### 3. Run the App

```bash
python app.py
```

Open your browser to: **http://localhost:8050/**

## Usage

### Import Transactions

1. Go to the **📥 Import** tab
2. Drag and drop (or click to select) your NatWest CSV file
3. Click **"Categorize Imported Transactions"**
   - Rules will match ~80-90% instantly (FREE)
   - AI will categorize the rest (if API key set)

### Review & Confirm

1. Go to the **📋 Review** tab
2. Filter by status: "Needs Review" shows uncategorized transactions
3. Review AI suggestions
4. (Future: Click to confirm/correct categories)

### View Statistics

1. Go to the **📊 Statistics** tab
2. See total transactions, categories, rules, and coverage

## NatWest CSV Format

The app expects NatWest CSV files with these columns:
- Date
- Type
- Description
- Value
- Balance
- Account Name
- Account Number

**Example:**
```
Date	Type	Description	Value	Balance	Account Name	Account Number
10-Jan-25	POS	TESCO STORES 1234	-45.67	1954.33	ALIKHAN A	757575-12344567
10-Jan-25	POS	STARBUCKS LONDON	-4.50	1949.83	ALIKHAN A	757575-12344567
```

## Default Rules

The app comes with **62 pre-configured rules** for common UK merchants:

**Groceries:** TESCO, SAINSBURY, ASDA, MORRISONS, WAITROSE, ALDI, LIDL, etc.
**Dining:** STARBUCKS, COSTA, PRET, GREGGS, MCDONALD, KFC, NANDO, etc.
**Transport:** TFL, UBER, TRAINLINE, SHELL, BP, ESSO, etc.
**Bills:** BRITISH GAS, BT GROUP, SKY, NETFLIX, SPOTIFY, etc.

These handle most common transactions instantly (FREE!).

## Troubleshooting

### Port Already in Use

If port 8050 is already in use, edit `app.py` line 636:

```python
app.run_server(debug=True, host='0.0.0.0', port=8051)  # Change to 8051
```

### Import Fails

Make sure your CSV is NatWest format (tab-separated). If you have a different bank format, we can add a parser for it.

### AI Not Working

1. Check API key is set: `echo $ANTHROPIC_API_KEY`
2. Check you have credits: https://console.anthropic.com/
3. Check internet connection

### Database Location

Database is created at: `personal-finance/data/finance.db`

To reset everything:
```bash
rm -rf data/finance.db
python app.py  # Will recreate with fresh categories/rules
```

## What's Next?

- **Manual category editing** - Click to change categories in UI
- **Rule creation** - One-click "Create rule from this transaction"
- **Spending dashboard** - Charts and trends
- **Budget tracking** - Set and monitor budgets
- **Export reports** - CSV/PDF exports

## Cost Estimates

**Rules-only mode (no API key):**
- Cost: $0.00 (FREE forever)
- Coverage: ~80-90% of typical transactions

**Hybrid mode (with API key):**
- Month 1 (500 txns, 0 rules): ~$0.05-0.10
- Month 3 (500 txns, 200 rules): ~$0.03-0.05
- Month 6 (500 txns, 400 rules): ~$0.01-0.02
- **System learns and gets cheaper!**

## Support

Questions? Issues? Email or create a GitHub issue.

---

**Happy budgeting! 💰**
