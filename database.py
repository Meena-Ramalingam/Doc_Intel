import os
import sqlite3
import mysql.connector

DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").lower()

DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_USER = os.environ.get("MYSQL_USER", "root")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
DB_NAME = os.environ.get("MYSQL_DATABASE", "docintel")

SQLITE_PATH = os.environ.get("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "docintel.db"))

def is_mysql():
	return DB_ENGINE == "mysql"

def get_connection(database=None):
	if is_mysql():
		return mysql.connector.connect(
			host=DB_HOST,
			user=DB_USER,
			password=DB_PASSWORD,
			database=database
		)
	# SQLite
	# Ensure file exists at project root
	db_dir = os.path.dirname(SQLITE_PATH)
	if db_dir and not os.path.exists(db_dir):
		os.makedirs(db_dir, exist_ok=True)
	if not os.path.exists(SQLITE_PATH):
		open(SQLITE_PATH, 'a').close()
	conn = sqlite3.connect(SQLITE_PATH, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
	conn.row_factory = sqlite3.Row
	return conn

def cursor(conn, dict=False):
	if is_mysql():
		if dict:
			return conn.cursor(dictionary=True)
		return conn.cursor()
	# SQLite uses Row factory; rows behave like dicts already
	return conn.cursor()

def ensure_database_and_tables():
	if is_mysql():
		conn = get_connection()
		conn.autocommit = True
		cur = conn.cursor()
		try:
			cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4")
		finally:
			cur.close()
			conn.close()

		conn = get_connection(DB_NAME)
		cur = conn.cursor()
		try:
			cur.execute("""
				CREATE TABLE IF NOT EXISTS users (
					id INT AUTO_INCREMENT PRIMARY KEY,
					name VARCHAR(100) NOT NULL,
					email VARCHAR(255) NOT NULL UNIQUE,
					password_hash VARCHAR(255) NOT NULL,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
			""")
			conn.commit()
		finally:
			cur.close()
			conn.close()
	else:
		conn = get_connection()
		cur = conn.cursor()
		try:
			cur.execute("""
				CREATE TABLE IF NOT EXISTS users (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					name TEXT NOT NULL,
					email TEXT NOT NULL UNIQUE,
					password_hash TEXT NOT NULL,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				);
			""")
			conn.commit()
		finally:
			cur.close()
			conn.close()