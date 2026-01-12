# Personal Finance Manager

AI-powered personal finance tool for transaction categorization and financial insights.

## Vision

A production-grade personal finance application that:
- Imports CSV bank statements and credit card exports
- Uses AI to auto-categorize transactions
- Provides manual review and correction workflow
- Generates insights and spending trends
- Helps understand your financial position

## Built on CasualHero BI Foundation

This tool leverages the successful patterns from CasualHero BI:
- ✅ Dash UI framework (proven, fast, professional)
- ✅ Polars for data processing (5-10x faster than pandas)
- ✅ Performance-first caching strategies
- ✅ Docker containerization
- ✅ Fly.io deployment patterns

## Tech Stack (Upgraded for Production)

### Backend
- **FastAPI** - Modern async Python framework (vs Flask/Gunicorn)
- **SQLite/DuckDB** - Local-first database (no cloud costs, privacy-first)
- **Polars** - High-performance data processing
- **Pydantic** - Data validation and settings management

### AI/ML
- **OpenAI API** - GPT-4 for transaction categorization
- **Or Local LLM** - Llama 3 for privacy-focused approach
- **Embeddings** - Semantic search for similar transactions

### Frontend
- **Dash** - Interactive dashboards (reuse CasualHero patterns)
- **Plotly** - Beautiful charts and visualizations
- **Bootstrap** - Professional styling

### Deployment
- **Docker** - Containerized deployment
- **Fly.io or Local** - Cloud or self-hosted

## Project Structure

```
personal-finance/
├── src/
│   ├── ui/           # Dash frontend (reused patterns from CasualHero)
│   ├── core/         # Business logic (categorization, rules engine)
│   ├── data/         # CSV import, database models, data processing
│   └── ml/           # AI categorization, embeddings, learning
├── tests/            # Comprehensive test suite
├── config/           # Configuration files, category mappings
├── uploads/          # Temporary CSV upload storage
├── Dockerfile        # Production-ready container
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Core Features (To Be Defined)

### Phase 1: MVP
- [ ] CSV import (multiple bank formats)
- [ ] Transaction parsing and normalization
- [ ] AI-powered categorization
- [ ] Manual review/correction interface
- [ ] Basic dashboard (spending by category)

### Phase 2: Intelligence
- [ ] Recurring transaction detection
- [ ] Budget tracking and alerts
- [ ] Spending trends and insights
- [ ] Merchant normalization (e.g., "AMZN MKTP" → "Amazon")

### Phase 3: Advanced
- [ ] Multi-account support
- [ ] Net worth tracking
- [ ] Investment portfolio integration
- [ ] Tax category tagging
- [ ] Export reports (CSV, PDF)

## Data Model (Draft)

### Transactions
```python
Transaction:
  - id: str (UUID)
  - date: date
  - description: str (raw from bank)
  - merchant: str (cleaned/normalized)
  - amount: Decimal
  - account: str
  - category: str (AI-suggested)
  - category_confidence: float (0.0-1.0)
  - category_confirmed: bool (user-approved)
  - tags: List[str]
  - notes: str
  - created_at: datetime
  - updated_at: datetime
```

### Categories
```python
Category:
  - id: str
  - name: str (e.g., "Groceries", "Dining", "Transport")
  - parent_id: str (optional, for hierarchies)
  - color: str (for UI)
  - icon: str (emoji or icon name)
  - budget_monthly: Decimal (optional)
```

### Rules
```python
Rule:
  - id: str
  - pattern: str (regex or keyword)
  - category_id: str
  - priority: int
  - created_at: datetime
```

## Key Questions for User

1. **CSV Format**: What banks/credit cards do you use? (to build parsers)
2. **Categories**: Do you have preferred categories or use existing taxonomy?
3. **AI Provider**: OpenAI API (paid, best quality) or Local LLM (free, privacy)?
4. **Deployment**: Run locally or deploy to cloud?
5. **Features Priority**: Which features are most important to you?
6. **Privacy**: Keep data local-only or OK with cloud database?

## Development Roadmap

### Week 1: Foundation
- [ ] Set up FastAPI backend
- [ ] Create SQLite/DuckDB schema
- [ ] Build CSV import pipeline
- [ ] Design category taxonomy

### Week 2: AI Integration
- [ ] Implement GPT-4/Llama categorization
- [ ] Build manual review UI (Dash)
- [ ] Create rules engine for automation

### Week 3: Dashboard & Insights
- [ ] Build spending dashboard
- [ ] Implement trend analysis
- [ ] Add budget tracking

### Week 4: Polish & Deploy
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Docker packaging
- [ ] Deployment (Fly.io or local)

## Success Metrics

- **Accuracy**: >90% correct AI categorization
- **Speed**: <1 second to process 1000 transactions
- **UX**: <5 clicks to import and review a month's transactions
- **Privacy**: All sensitive data encrypted at rest

---

**Next Steps**: Answer key questions above to start building!
