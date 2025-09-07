FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
ENV TESSERACT_CMD=/usr/bin/tesseract
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential libpq-dev libgl1 libglib2.0-0 tesseract-ocr tesseract-ocr-kor     wget unzip ca-certificates gnupg     && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -qO - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor | tee /etc/apt/keyrings/google-chrome.gpg > /dev/null
RUN echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && apt-get install -y google-chrome-stable --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install Chromedriver
# NOTE: This is a hardcoded version. It might need to be updated in the future.
# You can find the latest versions at https://googlechromelabs.github.io/chrome-for-testing/
ENV CHROMEDRIVER_VERSION="121.0.6167.85"
RUN wget -q https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip -O chromedriver.zip \
    && unzip chromedriver.zip -d / \
    && mv /chromedriver-linux64/chromedriver /usr/local/bin/ \
    && rm -rf /chromedriver-linux64 chromedriver.zip

COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 


RUN mkdir -p /app/media/timetables

# ★ CRLF 제거 후 실행권한 부여 (핵심)
COPY start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
