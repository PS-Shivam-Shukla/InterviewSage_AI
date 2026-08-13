# =========================================================
# Stage 1: Build Stage (Vite + TypeScript)
# =========================================================
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Environment build variables
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_WS_URL=ws://localhost/api/v1/ws

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL

RUN npm run build

# =========================================================
# Stage 2: Production Nginx Runtime Stage
# =========================================================
FROM nginx:1.25-alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html
COPY ../nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
