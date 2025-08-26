# ─── 1단계 ──────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# ★ 반드시 복사 ‼
COPY .env.production .

# 소스 전체 복사 후 빌드
COPY . .
RUN echo "### .env.production inside image ###" && \
    cat .env.production && \
    echo "####################################" && \
    npm run build

# ─── 2단계 ──────────────────────────
FROM nginx:stable-alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
