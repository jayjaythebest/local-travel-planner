import os
import json
from datetime import datetime

import gspread
from flask import Flask, jsonify, request
from flask_cors import CORS
from oauth2client.service_account import ServiceAccountCredentials

INDEX_HEADERS = [
    "名稱",
    "開始日期",
    "結束日期",
    "國家",
    "航班號",
    "出發機場",
    "出發時間",
    "抵達機場",
    "抵達時間",
    "酒店名稱",
    "酒店地址",
    "入住日期",
    "退房日期",
]
ITINERARY_HEADERS = ["日期", "開始時間", "結束時間", "活動", "地圖連結", "備註"]


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    spreadsheet = _init_spreadsheet()
    index_ws = _ensure_index_sheet(spreadsheet)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/trips")
    def list_trips():
        rows = index_ws.get_all_records()
        return jsonify(rows)

    @app.post("/api/trips")
    def create_trip():
        payload = request.get_json(force=True)
        name = payload.get("name", "").strip()
        start_date = payload.get("startDate", "").strip()
        end_date = payload.get("endDate", "").strip()
        country = payload.get("country", "").strip()

        if not all([name, start_date, end_date, country]):
            return jsonify({"error": "name/startDate/endDate/country are required"}), 400

        _validate_date(start_date)
        _validate_date(end_date)

        existing = [row.get("名稱") for row in index_ws.get_all_records()]
        if name in existing:
            return jsonify({"error": "Trip name already exists"}), 409

        ws = spreadsheet.add_worksheet(title=name, rows="200", cols=str(len(ITINERARY_HEADERS)))
        ws.append_row(ITINERARY_HEADERS)
        index_ws.append_row([name, start_date, end_date, country, "", "", "", "", "", "", "", "", ""])

        return jsonify({"ok": True, "trip": {"名稱": name, "開始日期": start_date, "結束日期": end_date, "國家": country}}), 201

    @app.get("/api/trips/<trip_name>/itinerary")
    def get_itinerary(trip_name: str):
        ws = spreadsheet.worksheet(trip_name)
        rows = ws.get_all_records(expected_headers=ITINERARY_HEADERS)
        return jsonify(rows)

    @app.post("/api/trips/<trip_name>/itinerary")
    def add_itinerary_item(trip_name: str):
        payload = request.get_json(force=True)
        item = [
            payload.get("日期", ""),
            payload.get("開始時間", ""),
            payload.get("結束時間", ""),
            payload.get("活動", ""),
            payload.get("地圖連結", ""),
            payload.get("備註", ""),
        ]
        if not item[0] or not item[3]:
            return jsonify({"error": "日期 and 活動 are required"}), 400

        ws = spreadsheet.worksheet(trip_name)
        ws.append_row(item)
        return jsonify({"ok": True}), 201

    return app


def _init_spreadsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    service_account_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "")
    sheet_id = os.environ.get("SHEET_ID", "")

    if not service_account_json or not sheet_id:
        raise RuntimeError("Missing GCP_SERVICE_ACCOUNT_JSON or SHEET_ID environment variables")

    creds_info = json.loads(service_account_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)


def _ensure_index_sheet(spreadsheet):
    try:
        ws = spreadsheet.worksheet("Index")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="Index", rows="200", cols=str(len(INDEX_HEADERS)))
        ws.append_row(INDEX_HEADERS)
    return ws


def _validate_date(raw_date: str):
    datetime.strptime(raw_date, "%Y-%m-%d")


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
