# Starting the SpendSenseAI Application

## Quick Start

### Option 1: Start Both Servers Together

```bash
python scripts/start_app.py
```

This will:
1. Start the API server on `http://localhost:8000`
2. Wait for it to be ready
3. Start the Operator Dashboard on `http://localhost:8501`
4. Open the dashboard in your browser automatically

### Option 2: Start Servers Separately

#### Terminal 1: Start API Server
```bash
python scripts/run_api.py
# or
uvicorn ui.api:app --reload --port 8000
```

#### Terminal 2: Start Dashboard
```bash
python scripts/run_dashboard.py
# or
streamlit run ui/dashboard.py --server.port 8501
```

## Access Points

- **API Server**: http://localhost:8000
  - Health Check: http://localhost:8000/health
  - API Docs: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

- **Operator Dashboard**: http://localhost:8501
  - Opens automatically when started
  - If not, navigate to http://localhost:8501 in your browser

## Prerequisites

1. **Database Setup**: Ensure `data/spendsense.db` exists with data
   ```bash
   # If database doesn't exist, load data first:
   python ingest/load_data.py --input data/processed/accounts.csv --format csv
   ```

2. **Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

## Troubleshooting

### API Server Not Starting

1. Check if port 8000 is already in use:
   ```bash
   netstat -ano | findstr :8000
   ```

2. Check database exists:
   ```bash
   if (Test-Path "data\spendsense.db") { Write-Host "Database exists" } else { Write-Host "Database not found" }
   ```

3. Check API logs for errors

### Dashboard Not Connecting to API

1. Verify API is running: http://localhost:8000/health
2. Check `API_BASE_URL` environment variable (default: `http://localhost:8000`)
3. Check browser console for connection errors

### Port Already in Use

Change ports in:
- API: Set `PORT` environment variable or modify `scripts/run_api.py`
- Dashboard: Use `--server.port` flag: `streamlit run ui/dashboard.py --server.port 8502`

## Stopping Servers

Press `Ctrl+C` in the terminal(s) where servers are running.

If using `start_app.py`, it will stop both servers automatically.

