FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
ENV TESSERACT_CMD=/usr/bin/tesseract
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential libpq-dev libgl1 libglib2.0-0 tesseract-ocr tesseract-ocr-kor wget unzip ca-certificates     && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -     && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list     && apt-get update     && apt-get install -y google-chrome-stable     && rm -rf /var/lib/apt/lists/*

# Install Chromedriver
RUN CHROME_VERSION=$(google-chrome --version | cut -d " " -f 3 | cut -d "." -f 1-3)     && CHROMEDRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION})     && wget -q https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip     && unzip chromedriver_linux64.zip -d /usr/local/bin/     && rm chromedriver_linux64.zip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/media/timetables

# ★ CRLF 제거 후 실행권한 부여 (핵심)
COPY start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
