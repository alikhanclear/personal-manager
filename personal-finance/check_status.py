from src.data.database import FinanceDatabase
from pathlib import Path

db = FinanceDatabase(Path('data/finance.db'))
txns = db.get_transactions()

total = len(txns)
uncategorized = len([t for t in txns if not t.category or t.category == 'Uncategorized'])
rule_matched = len([t for t in txns if t.category and t.category != 'Uncategorized' and t.category_confidence == 1.0])
ai_categorized = len([t for t in txns if t.category and t.category != 'Uncategorized' and t.category_confidence and t.category_confidence < 1.0])

print(f'Total Transactions: {total}')
print(f'Uncategorized: {uncategorized}')
print(f'Rule Matched (confidence=1.0): {rule_matched}')
print(f'AI Categorized (confidence<1.0): {ai_categorized}')
print()
print(f'Rules should have caught: {total - uncategorized}')
print(f'Still need AI: {uncategorized}')
