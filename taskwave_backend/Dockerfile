FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
ENV TESSERACT_CMD=/usr/bin/tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libgl1 libglib2.0-0 tesseract-ocr tesseract-ocr-kor \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/media/timetables

# ★ CRLF 제거 후 실행권한 부여 (핵심)
COPY start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
