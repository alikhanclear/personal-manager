# CasualHero BI Platform - Testing Guide

## Session 5: Dash Weekly Report Testing

**Server:** http://localhost:8050/

### Pre-Test Checklist

- [ ] Dash server is running (check terminal for "Dash is running on http://0.0.0.0:8050/")
- [ ] Data loaded successfully (should see "Ready! Loaded 1,657,933 transactions")
- [ ] No errors in terminal output

---

## Test 1: Home Page

**URL:** http://localhost:8050/

### Expected Results:
- [ ] Pink navbar (#FF6B9D) with "CasualHero BI Platform" logo
- [ ] Navigation links visible: Home, Weekly Report, Monthly Report, Trends
- [ ] Sidebar shows data summary:
  - Transactions count
  - Establishments count
  - Date range
  - Current fiscal period (FY2026 Week X)
- [ ] Three quick stats cards visible:
  - Total Orders
  - Total Sales (in £)
  - Establishments

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 2: Weekly Report - Page Load

**URL:** http://localhost:8050/weekly

### Expected Results:
- [ ] "Weekly Report" heading visible
- [ ] Fiscal Year dropdown populated (should show FY2021-FY2026)
- [ ] Default fiscal year selected (FY2026)
- [ ] Week dropdown populated (should show Week 1-52)
- [ ] Default week selected (latest week)
- [ ] Loading indicator appears briefly
- [ ] Report table loads successfully

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 3: Weekly Report - FY26 Week 4 (Power BI Comparison)

**Steps:**
1. Select "FY2026" from Fiscal Year dropdown
2. Select "Week 4" from Week dropdown
3. Wait for table to load

### Expected Results:

**Table Structure:**
- [ ] 14 columns visible:
  - Company, Establishment
  - Current Year Sales, Last Year Sales, Sales Var %
  - Current 4W Avg, Last 4W Avg, 4W Avg Var %
  - Current Vol, Last Vol, Vol Var %
  - Current ATV, Last ATV, ATV Var %

**Number Formatting:**
- [ ] Sales columns show whole numbers with commas (e.g., "12,345")
- [ ] ATV columns show 2 decimal places (e.g., "7.70", "9.36")
- [ ] Variance columns show 2 decimal places (e.g., "33.52", "-12.45")
- [ ] NO percentage symbols in variance columns (just the number)

**Conditional Formatting (Power BI Style):**
- [ ] Positive variance values have:
  - Light green background (#90EE90)
  - Dark green text (#006400)
- [ ] Negative variance values have:
  - Light pink/red background (#FFB6C1)
  - Dark red text (#8B0000)
- [ ] Applies to all 4 variance columns

**Sample Data Validation (compare with Power BI report):**
Find these establishments and verify values match:
- [ ] Meadowhall: ~£8,894 sales, ~1,155 orders, ~£7.70 ATV
- [ ] The O2: ~£8,737 sales, ~933 orders, ~£9.36 ATV
- [ ] Westfield: ~£18,629 sales, ~2,282 orders, ~£8.16 ATV

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 4: Interactive Features - Sorting

**Steps:**
1. Click on "Current Year Sales" column header
2. Click again to reverse sort

### Expected Results:
- [ ] First click: Sorts ascending (lowest to highest)
- [ ] Second click: Sorts descending (highest to lowest)
- [ ] Arrow icon appears in column header indicating sort direction
- [ ] Data reorders correctly
- [ ] Test other columns (Establishment, Sales Var %, etc.)

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 5: Interactive Features - Filtering

**Steps:**
1. Look for filter input boxes above each column
2. Type "Meadowhall" in Establishment filter box
3. Type ">10" in Sales Var % filter box

### Expected Results:
- [ ] Filter boxes visible above each column
- [ ] Typing filters the data instantly
- [ ] Establishment filter shows only matching rows
- [ ] Numeric filter (>10) shows only variance > 10%
- [ ] Clearing filter restores all data

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 6: Interactive Features - Pagination

**Steps:**
1. Look at bottom of table for pagination controls
2. Check "Rows per page" setting
3. Click "Next" button

### Expected Results:
- [ ] Pagination controls visible at bottom
- [ ] Shows "Page 1 of X" indicator
- [ ] Default: 20 rows per page
- [ ] "Next" button navigates to next page
- [ ] "Previous" button returns to previous page
- [ ] Can jump to specific page number

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 7: Interactive Features - Excel Export

**Steps:**
1. Look for "Export" button above table
2. Click "Export" button
3. Check downloads folder

### Expected Results:
- [ ] Export button visible and labeled
- [ ] Clicking triggers download
- [ ] File downloads as .xlsx (Excel format)
- [ ] File opens in Excel/LibreOffice successfully
- [ ] All columns included in export
- [ ] Filtered/sorted data exports correctly

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 8: Different Fiscal Weeks

**Steps:**
1. Select FY2026, Week 1
2. Select FY2025, Week 52
3. Select FY2024, Week 26

### Expected Results:
- [ ] Each week loads different data
- [ ] Report generation message shows timing (<100ms for cached data)
- [ ] No errors for any fiscal year/week combination
- [ ] Conditional formatting applies correctly for all weeks
- [ ] Data makes sense (no negative sales, ATV reasonable, etc.)

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 9: Performance

**Metrics:**
- [ ] Initial data load: ~80-120 seconds (acceptable)
- [ ] Report generation: <100ms (should be instant)
- [ ] Filtering: Instant response
- [ ] Sorting: Instant response
- [ ] Changing weeks: <100ms response

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Test 10: Responsive Design

**Steps:**
1. Resize browser window
2. Test on different screen sizes

### Expected Results:
- [ ] Table has horizontal scrollbar if needed (overflowX: auto)
- [ ] Navbar remains visible
- [ ] Sidebar adjusts appropriately
- [ ] All interactive features still work

**Status:** PASS / FAIL / NOT TESTED

**Notes:**

---

## Known Issues / Future Enhancements

- Monthly Report page: Shows "Coming soon..." (not implemented yet)
- Trends page: Shows "Coming soon..." (not implemented yet)
- Reload Data button in sidebar: Functionality to be tested
- Company totals: May need verification against Power BI
- Grand total row: May need verification against Power BI

---

## Critical Bugs to Report

If you encounter any of the following, report immediately:

1. **Data accuracy issues**: Numbers don't match Power BI report
2. **Conditional formatting broken**: Colors not showing correctly
3. **Number formatting issues**: Decimals wrong, commas missing
4. **Crash/errors**: Server crashes, Python errors in terminal
5. **Performance issues**: Report takes >1 second to load
6. **Interactive features broken**: Sorting, filtering, export not working

---

## Sign-Off

**Tester:** ___________________________

**Date:** ___________________________

**Overall Status:** PASS / FAIL / NEEDS REVISION

**Comments:**





---

**Next Steps After Testing:**
1. If all tests pass → Proceed to Monthly Report implementation
2. If issues found → Fix bugs, retest
3. Once stable → Deploy to Fly.io for production testing
