# Developer Guide - DocIntel

## Overview
Flask app provides auth + pages. Uploads are processed by running `backend.py` as a CLI with `--zip` and capturing JSON.

## Key Files
- app.py: Flask routes, sessions, login/signup, terms gating, upload handling, calls `backend.py` CLI and stores results.
- database.py: DB setup and connection helpers (SQLite default, MySQL optional).
- backend.py: OCR + PDF processing utilities and a CLI entry point to process a zip and print JSON records. FastAPI routes remain unused now.
- templates/login.html: Login form (POST /login).
- templates/signup.html: Sign-up form (POST /signup).
- templates/terms.html: Terms page; Accept posts to /terms/accept.
- templates/upload.html: Upload UI. Uses fetch to POST zip to /upload.
- templates/extract.html: Renders captured JSON records.
- templates/analysis.html: Shows summary table from records.
- static/css/style.css, static/images/2.png: Upload page styling and image.
- requirements.txt: Python dependencies.
- README.md: Setup and run instructions.

## Upload Flow
1. User logs in → accepts terms → visits /upload.
2. User selects .zip and submits. JS posts to `/upload` via fetch.
3. Flask saves file into `tmp_uploads/<filename>`.
4. Flask runs: `python backend.py --zip <temp_path>`.
5. `backend.py` reads the zip in memory, processes PDFs, prints JSON `{"records": [...]}`.
6. Flask parses JSON, saves to `session['last_records']`, deletes temp file.
7. Flask returns 200 to JS; browser redirects to `/extract`.

## backend.py CLI Contract
- Input: `--zip <path/to/zip>`
- Output: JSON to stdout: `{ "records": [ { "filename": str, "category": str, "classification_confidence": int, "extracted_fields": object, ... }, ... ] }`
- Should not print non-JSON to stdout on success.

## Styling
- Unified stylesheet `static/css/style.css` used across pages.
- Added shared `.card`, `.table-wrap`, and `table` styling for consistent UI.

## Extract Flow
- `POST /upload` saves the uploaded ZIP to `uploads/`, calls `process_zip_memory` (in-memory), writes CSV to `output/result_<timestamp>.csv`, and stores records in `session['last_records']`.
- `templates/extract.html` now renders records in a responsive table: filename, category, confidence, and key-value fields.
- Download via `/download.csv`.

## Backend Extraction
- `backend.py` depends only on `pdfplumber` and `pandas`.
- `process_zip_memory(BytesIO)` iterates PDFs in the ZIP and extracts text per page.

## Pages
- `upload.html`: pick .zip and submit via fetch to `/upload`.
- `extract.html`: tabular presentation of extracted results.
- `analysis.html` and `dashboard.html`: summary/links.

## Notes
- Tesseract path may need adjustment on Windows (set `pytesseract.pytesseract.tesseract_cmd`).
- FastAPI endpoints remain but are not required; the CLI path avoids a second server.
- Keep indentation (tabs) and code style consistent.
- Large PDFs: processing is synchronous; consider background jobs if needed.
