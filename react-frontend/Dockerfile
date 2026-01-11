# Multi-stage Dockerfile for Railway deployment

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --include=optional

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

# Copy nginx config for Railway (static serving only, no proxy)
COPY nginx.railway.conf /etc/nginx/conf.d/default.conf

# Railway expects port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
