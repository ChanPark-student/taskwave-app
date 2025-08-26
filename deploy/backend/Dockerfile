FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml poetry.lock ./
# backend/Dockerfile
RUN pip install --upgrade pip && \
    pip install "poetry>=1.7" && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi
                 #  ▲▲ --no-root 추가
 
COPY . .

EXPOSE 8000

CMD ["uvicorn", "demopj.main:app", "--host", "0.0.0.0", "--port", "8000"]
