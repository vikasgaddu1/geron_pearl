# PEARL Frontend Dockerfile - Multi-stage build
# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

# Cache bust argument - change this value to force npm reinstall
ARG CACHEBUST=7

# Copy package files (package-lock.json excluded via .dockerignore to avoid 
# platform-specific optional dependency issues between Windows dev and Linux deploy)
COPY package.json .npmrc ./

# Install dependencies fresh with Linux rollup binary
RUN echo "Cache bust: $CACHEBUST" && \
    npm install && \
    npm install @rollup/rollup-linux-x64-gnu @rollup/rollup-linux-x64-musl --save-optional

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Install envsubst (part of gettext)
RUN apk add --no-cache gettext

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config template and entrypoint
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Default backend URL (can be overridden by Railway env var)
ENV BACKEND_URL=http://backend.railway.internal:8000

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
