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
        # Reading the content of app.py to investigate potential issues
        app_py_path = os.path.join(main_folder_path, 'app.py')

        with open(app_py_path, 'r') as file:
            languages_data = file.read()

        # Displaying the first few lines of the app.py file for initial investigation
        languages_data[:1000]  # Displaying the first 1000 characters for a brief overview
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

        # Post-processing to fix hyphenation
        output_text = fix_hyphenation(output_text)

        # Save the result to a text file
        output_filename = f"{file_uuid}.txt"
        output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_filepath, 'w') as f:
            f.write(output_text)

        return output_filepath
    except Exception as e:
        logging.error(f"Error processing file {filepath}: {e}")
        return None

def fix_hyphenation(text):
    lines = text.split('\n')
    new_text = []
    for i in range(len(lines) - 1):
        line = lines[i].rstrip()
        next_line = lines[i + 1].lstrip()

        if line.endswith('-'):
            # Remove hyphen and join with the next line's first word
            new_text.append(line[:-1] + next_line.split(' ', 1)[0])

            # Update the next line by removing the joined word
            split_next_line = next_line.split(' ', 1)
            if len(split_next_line) > 1:
                lines[i + 1] = split_next_line[1]
            else:
                # If there's only one word on the next line, replace it with an empty string
                lines[i + 1] = ''
        else:
            new_text.append(line)

    # Add the last line if it wasn't processed
    if not lines[-1].startswith(' '):
        new_text.append(lines[-1])

    return '\n'.join(new_text)

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

