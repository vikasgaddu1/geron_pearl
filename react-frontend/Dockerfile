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

# Stage 2: Serve with lightweight server
FROM node:20-alpine AS runner

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Railway sets PORT dynamically
ENV PORT=3000

EXPOSE $PORT

# Serve the static files
CMD ["sh", "-c", "serve -s dist -l $PORT"]
