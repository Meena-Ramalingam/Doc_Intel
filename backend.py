import logging
import time
from io import BytesIO
import zipfile
import pdfplumber
import pandas as pd

logging.basicConfig(level=logging.INFO)

def classify_and_extraction(doc: str):
	# Minimal placeholder classification/extraction
	return ("Unclassified", 0, None)

def pdf_to_content(file_path: BytesIO, filename: str = "uploaded.pdf"):
	"""
	Extract text from a PDF using pdfplumber only (no OCR), and return a JSON-safe dict.
	"""
	if not file_path:
		raise ValueError("Invalid file path provided.")
	try:
		content_string = ""
		with pdfplumber.open(file_path) as pdf:
			metadata = pdf.metadata or {}
			meta_text = "\n".join([f"{k}: {v}" for k, v in metadata.items() if v])
			content_string += meta_text + "\n\n"
			for i, page in enumerate(pdf.pages):
				try:
					text = page.extract_text() or ""
					content_string += f"\n--- Page {i + 1} ---\n{text}\n|next page|\n\n"
				except Exception:
					pass
		content_string += "\n|end of file|\n"
		try:
			category, score, fields_df = classify_and_extraction(doc=content_string)
		except Exception:
			category, score, fields_df = ("Unclassified", 0, None)
		extracted_fields = {}
		if fields_df is not None:
			try:
				extracted_fields = (fields_df.to_dict(orient='records') or [{}])[0]
			except Exception:
				extracted_fields = {}
		return {
			"filename": filename.split("/")[-1],
			"category": category,
			"classification_confidence": int(score) if isinstance(score, (int, float)) else 0,
			"extracted_fields": extracted_fields,
			"content": content_string
		}
	except Exception:
		return None

def process_zip_memory(zip_memory: BytesIO):
	"""
	Read PDFs from an in-memory ZIP and return a DataFrame of extracted records.
	"""
	try:
		all_data = []
		with zipfile.ZipFile(zip_memory) as zip_file:
			pdf_filenames = [f for f in zip_file.namelist() if f.lower().endswith(".pdf")]
			for pdf_name in pdf_filenames:
				with zip_file.open(pdf_name) as pdf_file:
					pdf_bytes = pdf_file.read()
					pdf_data = pdf_to_content(BytesIO(pdf_bytes), pdf_name)
					if pdf_data:
						all_data.append(pdf_data)
				# brief pause to avoid blocking UI if very large
				time.sleep(0.01)
		return pd.DataFrame(all_data)
	except Exception:
		return None

   