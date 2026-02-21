# Streamlit -> React migration (keep Google Sheet schema)

This repo now includes a migration baseline that preserves your current Google Sheet structure:

- `Index` sheet headers remain:
  - 名稱, 開始日期, 結束日期, 國家, 航班號, 出發機場, 出發時間, 抵達機場, 抵達時間, 酒店名稱, 酒店地址, 入住日期, 退房日期
- Trip worksheet headers remain:
  - 日期, 開始時間, 結束時間, 活動, 地圖連結, 備註

## Added architecture

- `backend/api_server.py`
  - Flask API that reads/writes the same sheets using `gspread`
  - Endpoints:
    - `GET /api/trips`
    - `POST /api/trips`
    - `GET /api/trips/<trip_name>/itinerary`
    - `POST /api/trips/<trip_name>/itinerary`
- `frontend/` (React + Vite)
  - Sidebar trip management
  - Trip creation form
  - Itinerary creation form
  - Itinerary table view

## Run locally

1. Backend env vars:

```bash
export SHEET_ID="your_google_sheet_id"
export GCP_SERVICE_ACCOUNT_JSON='{"type":"service_account", ... }'
```

2. Start backend:

```bash
python backend/api_server.py
```

3. Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000`.

## Why this helps UX

- React gives smoother client-side interactions and state management.
- You can progressively add richer UI (timeline, drag/drop, expense charts) without changing your existing sheet layout.

## Download all files to your local machine

If you want one archive containing the React migration files plus all other repository files, run:

```bash
bash scripts/export_project_zip.sh
```

This creates:

- `dist/local-travel-planner-export.zip`

Then download/copy that zip to your local machine.

Optional custom output path and zip name:

```bash
bash scripts/export_project_zip.sh /tmp my-travel-planner.zip
```
