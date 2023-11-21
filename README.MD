Certainly! Below is a `README.md` template that documents the API of your Flask application. This documentation includes descriptions of the API endpoints, their expected inputs, and the outputs.

```markdown
# Tesseract OCR Flask API Documentation

This document provides detailed information about the API endpoints of the Flask application designed for OCR (Optical Character Recognition) using Tesseract.


Video Instruction:
[![Watch the video](https://img.youtube.com/vi/PaDWivzAMAM/maxresdefault.jpg)](https://youtu.be/PaDWivzAMAM)

## API Endpoints

### 1. Get Supported Languages

- **Endpoint:** `/languages`
- **Method:** `GET`
- **Description:** Returns a list of languages supported by the OCR service.
- **Response:**
  - **200 OK:** JSON containing the supported languages and their details.
  - **404 Not Found:** Error message if the `languages.json` file is not found.
  - **500 Internal Server Error:** Error message for any other internal errors.

### 2. Upload File for OCR

- **Endpoint:** `/upload`
- **Method:** `POST`
- **Description:** Uploads a file (PDF or image) for OCR processing.
- **Input:**
  - Form-data with:
    - `file`: The file to be processed.
    - `language` (optional): Language code for OCR (default is 'eng').
- **Response:**
  - **202 Accepted:** JSON containing the task ID and file UUID upon successful receipt of the file.
  - **400 Bad Request:** Error message if no file is provided or if the file is invalid.
  - **500 Internal Server Error:** Error message for any processing errors.

### 3. Download Processed Text

- **Endpoint:** `/download/<filename>`
- **Method:** `GET`
- **Description:** Downloads the OCR processed text file.
- **URL Parameters:**
  - `filename`: The name of the file to download.
- **Response:**
  - **200 OK:** The requested text file.
  - **404 Not Found:** Error message if the requested file is not found.

## Usage

### Getting Supported Languages

Request:
```
GET /languages
```

Response:
```json
[
  {
    "language_code": "eng",
    "language_name": "English",
    "traineddata_link": "https://..."
  },
  ...
]
```

### Uploading a File for OCR

Request:
```
POST /upload
Form-data:
  file: [file content]
  language: 'eng' (optional)
```

Response:
```json
{
  "message": "File received",
  "task_id": "task-uuid",
  "file_uuid": "file-uuid"
}
```

### Downloading Processed Text File

Request:
```
GET /download/file-uuid.txt
```

Response:
- The processed text file for download.

## Notes

- The OCR process is asynchronous. After uploading a file, use the provided `file_uuid` to download the processed text once it's ready.
- Ensure the uploaded file is in a supported format (PDF or image).
- For the list of supported languages, refer to the response from the `/languages` endpoint.
```

This README provides a concise yet comprehensive overview of your API, making it easier for users to understand how to interact with it. You can enhance this document by adding more details, examples, or clarifications as needed for your specific application.