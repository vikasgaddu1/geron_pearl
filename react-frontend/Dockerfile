# PEARL Frontend Dockerfile - Multi-stage build
# Stage 1: Build the React app (using debian-slim for glibc compatibility)
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files (package-lock.json excluded via .dockerignore)
COPY package.json .npmrc ./

# Install dependencies fresh - glibc Linux so standard rollup binary works
RUN npm install

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
