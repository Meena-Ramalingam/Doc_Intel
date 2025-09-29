# DocIntel Auth (Flask)

## Prerequisites
- Python 3.10+
- Optional: MySQL server if you want to use MySQL

## Quickstart (SQLite - default)
1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open `http://127.0.0.1:5000/` in your browser.

The SQLite database file `docintel.db` will be created in the project root on first run.

## Use MySQL instead of SQLite
Set environment variables before running the app:

- PowerShell (Windows):
  ```powershell
  $env:DB_ENGINE="mysql"
  $env:MYSQL_HOST="localhost"
  $env:MYSQL_USER="root"
  $env:MYSQL_PASSWORD="yourpassword"
  $env:MYSQL_DATABASE="docintel"
  ```

Ensure your MySQL server is running on port 3306. The app will create the `docintel` database and `users` table if they do not exist.

## Configuration
- `FLASK_SECRET_KEY` (default: `dev-secret-change-me`)
- `DB_ENGINE` (default: `sqlite`)
- `SQLITE_PATH` (default: `<project_root>/docintel.db`)

## Project Structure
```
app.py
database.py
requirements.txt
README.md
templates/
  login.html
  signup.html
```

## Notes
- Passwords are hashed using Werkzeug's `generate_password_hash`.
- Sessions are stored in secure Flask session cookies.
- Forms submit to `/signup` and `/login` and render server-side messages.

## Upload & Processing Flow (Flask-only)
- Upload page posts the selected .zip to `POST /upload`.
- `app.py` saves it to `tmp_uploads/`, invokes `backend.py --zip <path>` as a subprocess.
- `backend.py` processes PDFs and prints JSON to stdout; Flask stores results in session.
- `extract.html` renders JSON, `analysis.html` shows a table.

### Troubleshooting
- Ensure Tesseract is installed and on PATH if OCR is needed.
- Python deps: `pip install -r requirements.txt`.
- Logs: watch Flask console for errors during upload.

## UI and Styling
- All pages share `static/css/style.css`.
- Extract results are presented in a clean, responsive table in `templates/extract.html`.

## How to Use
1. Login → Accept terms → Dashboard → Upload.
2. Upload a `.zip` of PDFs; processing writes `output/result_<timestamp>.csv`.
3. Visit `Extract` to view a table; click Download CSV.

## Dependencies
Installed via `requirements.txt` (Flask, pdfplumber, pandas, Pillow, pypdfium2). FastAPI/LLM deps removed from upload flow.
