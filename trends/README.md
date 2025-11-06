# Google Trends Data Collection System

Isolated system for collecting and visualizing daily Google Trends data across 11 global regions.

## System Overview

**Architecture:**
- **Backend**: Flask API (port 5001) + pytrends + batch stitching
- **Frontend**: React + TypeScript + Vite (port 5173)
- **Storage**: JSON files per keyword per region
- **Data Format**: `[[timestamp_ms, value], ...]` (matches Dash oscillator standard)

**Features:**
- Add/delete keywords via Management tab
- Automatic fetch across 11 regions with batch stitching
- Status tracking (done/in-progress/failed with reasons)
- View trends by keyword (Word Charts) or by region (Region Charts)
- 60-second rate limiting to avoid IP blocking
- Initial scope: 6 months (upgradable to 3 years)

**11 Target Regions:**
1. New York Metro (`US-NY-501`)
2. Zurich Canton (`CH-ZH`)
3. Ireland (`IE`)
4. England (`GB-ENG`)
5. Mexico (`MX`)
6. Tokyo Prefecture (`JP-13`)
7. UAE (`AE`)
8. Nigeria (`NG`)
9. Maharashtra State (`IN-MH`)
10. Romania (`RO`)
11. Colombia (`CO`)
12. Beijing Municipality (`CN-11`)

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

### 1. Backend Setup

```bash
# Navigate to backend directory
cd trends/backend

# Install Python dependencies
pip install -r requirements.txt

# Start Flask API server
python app.py
```

Backend will run on `http://localhost:5001`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd trends/frontend

# Install npm dependencies (if not already done)
npm install

# Start Vite dev server
npm run dev
```

Frontend will run on `http://localhost:5173`

---

## Usage Guide

### Adding Keywords

1. Open frontend: `http://localhost:5173`
2. Go to **Management** tab
3. Enter keyword in input field (e.g., "bitcoin", "ethereum")
4. Click **Add** button
5. System will automatically:
   - Fetch data for all 11 regions
   - Stitch batches if needed (6 months = 1 batch)
   - Save to JSON files
   - Update status

**Note**: Fetching takes ~44 minutes for 6 months (11 regions × 4 batches × 60 seconds). For 6 months, it's ~11 minutes (11 regions × 1 batch × 60 seconds).

### Viewing Trends

**Word Charts Tab:**
- Select keyword from dropdown
- View trend lines for all 11 regions
- Y-axis: 0-100 (Google Trends normalized scale)
- X-axis: Dates

**Region Charts Tab:**
- Select region from dropdown
- View trend lines for all keywords
- Same chart format as Word Charts

### Deleting Keywords

1. Go to **Management** tab
2. Click **×** button next to keyword
3. Confirm deletion
4. All associated data files will be deleted

---

## Configuration

### Timeframe Settings

To upgrade from 6 months to 3 years:

**File**: `backend/config.py`

```python
# Change this line:
FETCH_DAYS = 180  # 6 months

# To:
FETCH_DAYS = 1095  # 3 years
```

**Note**: 3-year fetches take ~44 minutes per keyword (4 batches × 11 regions × 60 seconds).

### Region Codes

Edit `backend/config.py` to add/modify regions. See `GEO_CODES` dictionary.

**Important**: City-level granularity only available for US metros. International locations use country/region codes.

### Rate Limiting

Default: 60 seconds between requests

**File**: `backend/config.py`

```python
MIN_REQUEST_INTERVAL = 60  # seconds
```

**Warning**: Reducing below 60 seconds may trigger Google IP blocking.

---

## File Structure

```
trends/
├── backend/
│   ├── app.py                    # Flask API server
│   ├── config.py                 # Configuration (geo codes, settings)
│   ├── requirements.txt
│   │
│   ├── data/
│   │   ├── trends_fetcher.py    # Pytrends + batch stitching
│   │   ├── trends_manager.py    # Keyword CRUD
│   │   ├── storage.py           # JSON utilities
│   │   └── __init__.py
│   │
│   ├── historical_data/
│   │   ├── trends_{keyword}_{region}.json
│   │   └── ... (auto-generated)
│   │
│   └── metadata/
│       ├── keywords.json         # Keyword metadata
│       └── fetch_status.json     # Fetch log
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Management.tsx    # Tab 1: Keyword CRUD
    │   │   ├── WordCharts.tsx    # Tab 2: Charts by keyword
    │   │   └── RegionCharts.tsx  # Tab 3: Charts by region
    │   │
    │   ├── lib/
    │   │   └── api.ts            # API client
    │   │
    │   ├── App.tsx               # Main app
    │   ├── main.tsx
    │   └── index.css             # Dash dark theme
    │
    ├── package.json
    └── vite.config.ts
```

---

## API Endpoints

### Keywords
- `GET /api/keywords` - List all keywords
- `POST /api/keywords` - Add keyword (triggers fetch)
- `DELETE /api/keywords/<id>` - Delete keyword

### Trend Data
- `GET /api/trends/<keyword>` - Get data for keyword (all regions)
- `GET /api/trends/<keyword>/<region>` - Get data for keyword+region
- `GET /api/trends/region/<region>` - Get data for region (all keywords)

### Metadata
- `GET /api/regions` - List all 11 configured regions
- `GET /api/status/<keyword_id>` - Get fetch status
- `GET /api/health` - Health check

---

## Technical Details

### Google Trends API Limitations

**Daily Data Limit**: 270 days per request

**Solution**: Batch stitching with overlap normalization
- 6 months = 1 batch (180 days)
- 3 years = 4 batches (270+270+270+285 days with 1-day overlaps)

**Algorithm**:
1. Split date range into 270-day batches
2. Fetch each batch separately (60s delay between)
3. Normalize using overlap values as adjustment anchors
4. Stitch into seamless dataset

### Data Format

**Storage**: `trends_{keyword}_{region}.json`

```json
[
  [1667865600000, 45.2],
  [1667952000000, 48.7],
  [1668038400000, 52.1],
  ...
]
```

- Timestamps: Milliseconds Unix epoch
- Values: 0-100 (Google Trends normalized scale)

### Status Tracking

**Keyword Status**:
- `completed`: All 11 regions fetched successfully
- `partial`: Some regions failed
- `failed`: All regions failed
- `in_progress`: Currently fetching

**Fetch Log** (`metadata/fetch_status.json`):
```json
{
  "keyword_id": "uuid",
  "keyword": "bitcoin",
  "region": "US-NY-501",
  "status": "completed",
  "fetched_at": "2025-11-06T12:00:00Z",
  "error": null,
  "data_points": 180
}
```

---

## Troubleshooting

### Backend won't start
- Check port 5001 is not in use: `netstat -ano | findstr :5001`
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

### Frontend won't start
- Check port 5173 is not in use
- Install dependencies: `npm install`
- Check Node version: `node --version` (need 18+)

### Google blocking requests
- **Symptom**: "Too many requests" errors
- **Solution**: Increase `MIN_REQUEST_INTERVAL` in config.py
- **Prevention**: Don't add too many keywords at once

### No data showing in charts
- Check keyword status in Management tab
- Verify backend is running: `http://localhost:5001/api/health`
- Check browser console for errors

### Charts render incorrectly
- Ensure all dependencies installed: `npm install`
- Clear browser cache and reload
- Check for errors in browser console

---

## Future Enhancements

- [ ] Add APScheduler for daily automatic updates
- [ ] Proxy rotation for rate limit mitigation
- [ ] Export charts to PNG/CSV
- [ ] Date range selector for chart filtering
- [ ] Progress bar for fetch operations
- [ ] Retry logic for failed regions
- [ ] Real-time status updates via WebSocket

---

## Notes

**Isolation**: This system is completely separate from the main Dash app. No shared code or dependencies.

**Data Quality**: Google Trends values are relative (0-100 scale normalized to peak in timeframe), not absolute search volumes.

**City-Level Limitation**: Only US metros have city-level granularity. International locations use country/region codes.

**Rate Limits**: Google Trends has undocumented rate limits. Stick to 60-second intervals to avoid IP blocking.

---

## Support

For issues or questions, refer to:
- pytrends documentation: https://github.com/GeneralMills/pytrends
- Recharts documentation: https://recharts.org
- React + Vite: https://vitejs.dev/guide/

---

**System Status**: ✅ MVP Complete (6-month historical data, manual updates)

**Upgrade Path**: Change `FETCH_DAYS = 1095` in config.py for 3-year historical data
