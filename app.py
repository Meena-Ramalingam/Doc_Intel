import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection, ensure_database_and_tables, cursor, is_mysql, DB_NAME
import tempfile
import shutil
import requests
import subprocess
import socket
import json
import csv
from io import StringIO, BytesIO
import sys
import time
import glob
from backend import process_zip_memory


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

ensure_database_and_tables()

def db_conn_for_app():
	if is_mysql():
		return get_connection(DB_NAME)
	return get_connection()

def param_placeholder():
	return "%s" if is_mysql() else "?"

@app.route("/")
def index():
	if "user_id" in session:
		return redirect(url_for("home"))
	return redirect(url_for("login"))

@app.route("/home")
def home():
	if "user_id" not in session:
		return redirect(url_for("login"))
	name = session.get("user_name", "User")
	return f"Welcome, {name}! <a href='{url_for('logout')}'>Logout</a>"

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")

		if not email or not password:
			return render_template("login.html", error="Email and password are required.")

		conn = db_conn_for_app()
		cur = cursor(conn, dict=True)
		try:
			q = f"SELECT id, name, email, password_hash FROM users WHERE email={param_placeholder()}"
			cur.execute(q, (email,))
			user = cur.fetchone()
		finally:
			cur.close()
			conn.close()

		if not user:
			return render_template("login.html", error="Invalid email or password.")

		# `user` is dict-like for both backends
		if not check_password_hash(user["password_hash"], password):
			return render_template("login.html", error="Invalid email or password.")

		session["user_id"] = user["id"]
		session["user_name"] = user["name"]
		session["user_email"] = user["email"]
		return redirect(url_for("terms"))

	return render_template("login.html", error=None)

@app.route("/signup", methods=["GET", "POST"])
def signup():
	if request.method == "POST":
		name = request.form.get("name", "").strip()
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")

		if not name or not email or not password:
			return render_template("signup.html", error="All fields are required.", success=None)

		conn = db_conn_for_app()
		cur = cursor(conn, dict=True)
		try:
			q_exists = f"SELECT 1 AS exists_flag FROM users WHERE email={param_placeholder()}"
			cur.execute(q_exists, (email,))
			exists = cur.fetchone()
			if exists:
				return render_template("signup.html", error="Email already registered.", success=None)

			password_hash = generate_password_hash(password)
			q_insert = f"INSERT INTO users (name, email, password_hash) VALUES ({param_placeholder()}, {param_placeholder()}, {param_placeholder()})"
			cur.execute(q_insert, (name, email, password_hash))
			conn.commit()
		finally:
			cur.close()
			conn.close()

		return render_template("signup.html", error=None, success="Account created! You can now log in.")

	return render_template("signup.html", error=None, success=None)

@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("login"))

@app.route("/terms", methods=["GET"])
def terms():
	if "user_id" not in session:
		return redirect(url_for("login"))
	return render_template("terms.html")

@app.route("/terms/accept", methods=["POST"])
def accept_terms():
	if "user_id" not in session:
		return redirect(url_for("login"))
	session["accepted_terms"] = True
	return redirect(url_for("upload"))

@app.route("/upload", methods=["GET"])
def upload():
	if "user_id" not in session:
		return redirect(url_for("login"))
	if not session.get("accepted_terms"):
		return redirect(url_for("terms"))
	return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_post():
	if "user_id" not in session:
		return redirect(url_for("login"))
	if not session.get("accepted_terms"):
		return redirect(url_for("terms"))
	# Integrate provided upload processing
	if "file" not in request.files:
		return ("No file part named 'file' in form.", 400)
	f = request.files.get("file")
	if f.filename == "":
		return ("No selected file.", 400)
	if not f.filename.lower().endswith(".zip"):
		return ("Only .zip files are allowed.", 400)

	try:
		os.makedirs("uploads", exist_ok=True)
		os.makedirs("output", exist_ok=True)
		upload_path = os.path.join("uploads", f.filename)
		f.save(upload_path)

		with open(upload_path, "rb") as fh:
			data = fh.read()
		df = process_zip_memory(BytesIO(data))
		if df is None or getattr(df, "empty", True):
			return ("No PDF data extracted from the uploaded ZIP.", 400)

		# Save CSV like reference flow
		ts = time.strftime("%Y%m%d_%H%M%S")
		out_csv = os.path.join("output", f"result_{ts}.csv")
		df.to_csv(out_csv, index=False)

		# Preserve existing behavior for templates that read session
		try:
			session["last_records"] = df.to_dict(orient="records")
		except Exception:
			session["last_records"] = []

		if request.headers.get("X-Requested-With") == "fetch":
			return ("OK", 200)
		return redirect(url_for("extract"))
	except Exception as e:
		return (str(e), 500)

@app.route("/analysis")
def analysis():
	data = session.get("last_records", [])
	return render_template("analysis.html", data=data)

@app.route("/extract")
def extract():
	data = session.get("last_records", [])
	return render_template("extract.html", data=data)

@app.route("/dashboard")
def dashboard():
	data = session.get("last_records", [])
	return render_template("dashboard.html", data=data)

@app.route("/download.csv")
def download_csv():
	data = session.get("last_records", [])
	si = StringIO()
	if data:
		fieldnames = sorted({k for rec in data for k in rec.keys()})
		writer = csv.DictWriter(si, fieldnames=fieldnames)
		writer.writeheader()
		for rec in data:
			writer.writerow(rec)
	response = app.response_class(si.getvalue(), mimetype="text/csv")
	response.headers["Content-Disposition"] = "attachment; filename=result.csv"
	return response


if __name__ == "__main__":
	app.run(debug=True)