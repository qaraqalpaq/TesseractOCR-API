FROM python:3.9-slim

# Install Tesseract OCR, Poppler, wget, jq, and other dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    wget \
    jq \
    && apt-get clean

WORKDIR /app

# Create tessdata directory with appropriate permissions
RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata && \
    chmod -R 777 /usr/share/tesseract-ocr/4.00/tessdata

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00
# Copy languages.json, the script, and the application code
COPY languages.json .
COPY app.py .

CMD ["python", "app.py"]
