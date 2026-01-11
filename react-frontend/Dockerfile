# Multi-stage Dockerfile for Railway deployment

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for Vite (passed at build time)
ARG VITE_API_BASE_URL=""
ARG VITE_WS_URL=""

# Set as environment variables for the build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Build the app
RUN npm run build

# Stage 2: Serve with nginx (tiny image, no npm needed)
FROM nginx:alpine AS runner

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config template (uses $PORT variable)
COPY nginx.railway.conf /etc/nginx/nginx.conf.template

# Railway sets PORT dynamically (default 80 for local testing)
ENV PORT=80

# Substitute PORT and start nginx
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
