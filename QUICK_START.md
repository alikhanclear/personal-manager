# CasualHero BI Platform - Quick Start

## Start the Server

```bash
cd "C:\Users\azimu\Documents\012. Casual Hero"
python src/ui/dash_app.py
```

**Wait for:** "Dash is running on http://0.0.0.0:8050/"

---

## Access the Dashboard

**URL:** http://localhost:8050/

---

## Navigation

- **Home:** Dashboard overview with quick stats
- **Weekly Report:** Interactive YoY comparison table
- **Monthly Report:** Coming soon
- **Trends:** Coming soon

---

## Weekly Report Features

### Selectors
- **Fiscal Year:** FY2021 - FY2026
- **Week:** Week 1 - Week 52

### Table Features
- **Sort:** Click column headers
- **Filter:** Use search boxes above columns
- **Paginate:** 20 rows per page (controls at bottom)
- **Export:** Click "Export" button for Excel download

### What to Look For
- ✅ Green backgrounds = positive variance (good performance)
- ✅ Red backgrounds = negative variance (needs attention)
- ✅ Numbers formatted with commas (12,345)
- ✅ ATV with 2 decimals (7.70, 9.36)
- ✅ Variance with 2 decimals (33.52, -12.45)

---

## Test with Power BI Data

**Select:** FY2026, Week 4

**Find these establishments:**
- Meadowhall: ~£8,894 sales, ~1,155 orders, ~£7.70 ATV
- The O2: ~£8,737 sales, ~933 orders, ~£9.36 ATV
- Westfield: ~£18,629 sales, ~2,282 orders, ~£8.16 ATV

---

## Files

- `src/ui/dash_app.py` - Main Dash application
- `src/core/kpi_calculator.py` - Business logic
- `TESTING_GUIDE.md` - Full test plan
- `SESSION_5_SUMMARY.md` - What we accomplished
- `CLAUDE.md` - Full project documentation

---

## Troubleshooting

**Server won't start:**
- Check .env file has DATABASE_URL
- Verify dependencies: `pip install -r requirements.txt`

**Slow performance:**
- First load takes ~80-120s (normal)
- Reports should be <100ms after initial load

**Data doesn't match Power BI:**
- Check fiscal year/week selected
- Verify payment status filter (captured/authorized only)
- Review KPI calculations in kpi_calculator.py

---

## Next Steps

1. Test the Weekly Report
2. Report any bugs or issues
3. Provide Monthly Report structure
4. Provide Power BI DAX measures for validation

---

**Need Help?** Check CLAUDE.md for full context
