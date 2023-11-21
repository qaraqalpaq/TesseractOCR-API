from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from celery import Celery
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import uuid
import json
import os
import logging


app = Flask(__name__)

# Configure directories
UPLOAD_FOLDER = '/mnt/data/uploads'
OUTPUT_FOLDER = '/mnt/data/outputs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Check and create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Celery configuration
app.config['broker_url'] = 'redis://redis:6379/0'
app.config['result_backend'] = 'redis://redis:6379/0'
app.config['broker_connection_retry_on_startup'] = True
celery = Celery(app.name, broker=app.config['broker_url'])
celery.conf.update(app.config)

@app.route('/languages', methods=['GET'])
def get_languages():
    try:
        with open('languages.json', 'r') as file:
            languages_data = file.read()
        return jsonify(json.loads(languages_data)), 200
    except FileNotFoundError:
        return jsonify({"error": "Languages file not found"}), 404
    except Exception as e:
        logging.error(f"Error reading languages file: {e}")
        return jsonify({"error": "An error occurred while reading the file"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    language = request.form.get('language', 'eng')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Generate a unique UUID for the file
    file_uuid = str(uuid.uuid4())
    filename = secure_filename(f"{file_uuid}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    task = process_ocr.delay(filepath, language, file_uuid)
    return jsonify({"message": "File received", "task_id": task.id, "file_uuid": file_uuid}), 202


@celery.task
def process_ocr(filepath, language, file_uuid):
    try:
        # Specify the Tesseract command and tessdata directory
        tessdata_dir = '/usr/share/tesseract-ocr/4.00/tessdata'
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        custom_config = f'--tessdata-dir {tessdata_dir} --oem 1 -l {language}'

        # Check if the file is a PDF
        if filepath.endswith('.pdf'):
            images = convert_from_path(filepath)
            output_text = ''.join(pytesseract.image_to_string(img, config=custom_config) for img in images)
        else:
            output_text = pytesseract.image_to_string(Image.open(filepath), config=custom_config)

        # Save the result to a text file
        output_filename = f"{file_uuid}.txt"
        output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_filepath, 'w') as f:
            f.write(output_text)

        return output_filepath
    except Exception as e:
        logging.error(f"Error processing file {filepath}: {e}")
        return None

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

