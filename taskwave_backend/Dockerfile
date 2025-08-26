FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 시스템 패키지: 빌드 도구, Postgres, OpenCV 런타임, Tesseract(+한글)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-kor \
 && rm -rf /var/lib/apt/lists/*

# 파이썬 라이브러리
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스
COPY . .

# media 폴더(로컬 스토리지 시 사용)
RUN mkdir -p /app/media/timetables

# 시작 스크립트
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
