# NewsSentimentAgent - Intelligent Sentiment Analysis

## 🎯 Overview

An intelligent financial sentiment analysis agent that **automatically discovers and queries** data from Google Cloud Storage or local filesystem. No manual file management required!

### **Key Features:**
- ✅ **Automatic file discovery** - Finds all data files without configuration
- ✅ **Intelligent categorization** - Organizes files by purpose (news, analyst, etc.)
- ✅ **Multi-source analysis** - Combines news, analyst ratings, and transcripts
- ✅ **GCS & Local support** - Works with cloud storage or local files
- ✅ **Credit risk focus** - Designed for fixed-income analysts
- ✅ **Source attribution** - Always tracks which files were used

---

## 🚀 Quick Start

### **1. Setup Environment**

```bash
# Create .env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

```bash
# .env
GCS_DATA_BUCKET=gs://your-bucket-name
GCS_DATASET_PREFIX=datasets/uc4-market-activity-prediction-agent
GOOGLE_CLOUD_PROJECT=your-project-id
ENVIRONMENT=development
```

### **2. Authenticate**

```bash
gcloud auth application-default login
```

### **3. Install Dependencies**

```bash
uv pip install gcsfs pandas python-dotenv
```

### **4. Test the Agent**

```bash
# Quick validation
python test_agent_quick.py

# Full GCS tests
pytest tests/integration/test_gcs_connection.py -v -s
```

### **5. Run the Agent**

```bash
make playground
```

---

## 💬 Example Queries

### **Simple Sentiment Analysis:**
```
"Analyze this headline: Tesla recalls 2M vehicles"
```

### **Company Analysis:**
```
"What's the sentiment for Apple?"
"Give me comprehensive sentiment for NVDA"
```

### **Analyst Trends:**
```
"What are analysts saying about Microsoft?"
"Show me analyst sentiment for TSLA"
```

### **Market Statistics:**
```
"What's the overall market sentiment?"
"Show me sentiment distribution"
```

### **Credit-Focused:**
```
"Does this headline indicate credit risk: Boeing faces $2B penalty?"
"Credit implications of Apple earnings beat"
```

---

## 🏗️ Architecture

### **Intelligent Data Discovery**

```
Initialization:
├── Check GCS_DATA_BUCKET configuration
├── Connect to GCS (or use local filesystem)
├── Discover all files in dataset folder
├── Categorize files by purpose:
│   ├── News headlines
│   ├── Analyst ratings
│   ├── Earnings transcripts
│   ├── Market data
│   └── Company metadata
└── Build searchable catalog
```

### **Query Flow**

```
User Query → Agent → Tool Selection → Smart Query → File Discovery
                                                    ↓
                                            Automatic Filtering
                                                    ↓
                                              Data Combination
                                                    ↓
                                            Source Tracking
                                                    ↓
                                         ← Results with Attribution
```

---

## 🛠️ Available Tools

### **1. analyze_news_headline(headline)**

**What it does:**
- Searches ALL discovered news files
- Finds matching or similar headlines
- Returns sentiment with confidence

**Example:**
```python
analyze_news_headline("Apple posts record earnings")

# Returns:
{
    "sentiment": "positive",
    "confidence": "high",
    "source_files": ["stock_news.csv"],
    "total_searched": 26000
}
```

### **2. analyze_analyst_sentiment(ticker, days_lookback)**

**What it does:**
- Finds analyst rating files automatically
- Filters by ticker
- Analyzes upgrade/downgrade trends

**Example:**
```python
analyze_analyst_sentiment("AAPL", days_lookback=90)

# Returns:
{
    "ticker": "AAPL",
    "sentiment": "positive",
    "upgrades": 15,
    "downgrades": 3,
    "total_ratings": 25
}
```

### **3. get_comprehensive_sentiment(ticker)**

**What it does:**
- Queries ALL relevant data sources
- Combines news + analyst + transcripts
- Provides multi-source analysis

**Example:**
```python
get_comprehensive_sentiment("MSFT")

# Returns:
{
    "ticker": "MSFT",
    "sentiment_summary": {
        "news": {...},
        "analyst": {...}
    },
    "data_sources_used": ["stock_news.csv", "analyst_ratings_processed.csv"],
    "overall_sentiment": "positive"
}
```

### **4. get_sentiment_statistics(source)**

**What it does:**
- Analyzes market-wide trends
- Returns sentiment distribution
- Performance optimized

**Example:**
```python
get_sentiment_statistics("all")

# Returns:
{
    "sources": {
        "news": {
            "total_articles": 26000,
            "sentiment_distribution": {"positive": 8000, "negative": 12000, ...}
        }
    }
}
```

---

## 📊 Supported Data Files

The agent automatically discovers and uses these files:

### **Sentiment Sources:**
- `stock_news.csv` - News headlines with labels
- `analyst_ratings_processed.csv` - Analyst recommendations
- `earnings-call-transcripts-*/` - Earnings call transcripts

### **Market Data:**
- `30_yr_stock_market_data.csv` - Historical prices
- `indexData.csv` - Market indices
- `US_Economic_Indicators.csv` - Economic indicators

### **Company Information:**
- `sp500_companies.csv` - S&P 500 constituents
- `symbols_valid_meta.csv` - Ticker metadata

### **Corporate Actions:**
- `acquisitions_update_2021.csv` - M&A activity
- `communications.csv` - Corporate filings

---

## 🧪 Testing

### **Quick Test:**
```bash
python test_agent_quick.py
```

### **GCS Connection Tests:**
```bash
# Full diagnostic
pytest tests/integration/test_gcs_connection.py::test_comprehensive_gcs_report -v -s

# List all files in bucket
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_list_all_dataset_files -v -s

# Test specific file reading
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_read_index_data_csv -v -s
```

### **Explore Bucket:**
```bash
python scripts/list_bucket_contents.py
```

---

## 🔧 Configuration

### **Environment Variables:**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GCS_DATA_BUCKET` | No* | GCS bucket path | `gs://your-bucket` |
| `GCS_DATASET_PREFIX` | Yes | Dataset folder | `datasets/uc4-...` |
| `GOOGLE_CLOUD_PROJECT` | Yes | GCP project ID | `your-project-id` |
| `ENVIRONMENT` | No | Environment | `development` |

*If not set, uses local filesystem

### **Local Development:**

Leave `GCS_DATA_BUCKET` empty in `.env`:
```bash
GCS_DATA_BUCKET=
```

Place data files in:
```
my-agent/app/dataset/
├── stock_news.csv
├── analyst_ratings_processed.csv
└── ...
```

---

## 🐛 Troubleshooting

### **"No data files discovered"**

**Possible causes:**
1. GCS_DATA_BUCKET not set or incorrect
2. Authentication issues
3. Files in different location

**Fix:**
```bash
# Check .env configuration
cat .env

# Verify authentication
gcloud auth application-default login

# Test GCS access
pytest tests/integration/test_gcs_connection.py::test_bucket_access -v -s
```

### **"No data found for ticker"**

**Possible causes:**
1. Ticker doesn't exist in dataset
2. Ticker spelled incorrectly
3. Data files don't have that ticker

**Fix:**
```bash
# Check what tickers are available
python scripts/list_bucket_contents.py

# Try a different ticker like AAPL, MSFT, GOOGL
```

### **"Tool returns empty results"**

**Possible causes:**
1. Filters too restrictive
2. Data quality issues
3. File format unexpected

**Fix:**
```python
# Check the raw data
from app.sub_agents.news_sentiment_agent.tools import data_store
df = data_store.smart_query('news')
print(df.head())
print(df.columns)
```

---

## 📚 Documentation

- **Implementation Details:** `AGENT_IMPLEMENTATION_SUMMARY.md`
- **GCS Quick Start:** `GCS_QUICKSTART.md`
- **GCS Tests:** `tests/integration/README_GCS_TESTS.md`
- **Scripts:** `scripts/README.md`

---

## 🎯 Design Principles

### **1. Zero Configuration**
Agent automatically discovers available data - no file paths to configure.

### **2. Intelligent Selection**
System determines which files to query based on user intent.

### **3. Multi-Source Intelligence**
Automatically combines data from multiple sources for comprehensive analysis.

### **4. Transparency**
Always reports which data sources were used.

### **5. Graceful Degradation**
Works with GCS or local files, handles missing data gracefully.

---

## 🚀 Advanced Usage

### **Custom Filters:**
```python
data_store.smart_query(
    'news',
    filters={
        'ticker': 'AAPL',
        'sentiment': 'negative',
        'start_date': '2020-01-01'
    }
)
```

### **Intent-Based Queries:**
```python
# Get all economic data
data_store.smart_query('economic')

# Get company information
data_store.smart_query('company')

# Get everything for comprehensive analysis
data_store.smart_query('comprehensive', filters={'ticker': 'TSLA'})
```

### **File Catalog Access:**
```python
from app.sub_agents.news_sentiment_agent.tools import data_store

# See what's available
catalog = data_store.file_catalog

print("News files:", catalog['sentiment_sources']['news'])
print("Analyst files:", catalog['sentiment_sources']['analyst'])
```

---

## 💡 Tips

1. **Start Simple:** Test with `analyze_news_headline()` first
2. **Use Comprehensive:** For full analysis, use `get_comprehensive_sentiment()`
3. **Check Sources:** Review `data_sources_used` in results
4. **Local Testing:** Set GCS_DATA_BUCKET="" for local development
5. **Performance:** System caches file catalog for speed

---

## ✅ Success Checklist

- [ ] `.env` file configured
- [ ] GCS authentication working
- [ ] `test_agent_quick.py` passes
- [ ] GCS tests pass
- [ ] Agent starts with `make playground`
- [ ] Can query for sentiment
- [ ] Results include source attribution

---

## 🆘 Getting Help

If you encounter issues:

1. Run `python test_agent_quick.py` for diagnostics
2. Check `tests/integration/README_GCS_TESTS.md` for GCS help
3. Review `AGENT_IMPLEMENTATION_SUMMARY.md` for architecture
4. Test GCS connection with provided test suite

---

## 🎉 You're Ready!

Your intelligent sentiment agent is configured and ready to analyze financial data with automatic data discovery!

Start the playground:
```bash
make playground
```

Then try:
```
"What's the sentiment for Apple?"
```

The agent will automatically find and analyze all relevant data! 🚀
