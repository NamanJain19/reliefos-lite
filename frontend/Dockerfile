# ==============================================================================
# RELIEFOS Lite — Production Frontend Container
# Multi-stage build with Node.js 20 builder and lightweight Alpine Nginx runner
# ==============================================================================

# Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install package dependencies
COPY package*.json ./
RUN npm ci

# Copy source code and build production assets
COPY . .
RUN npm run build

# Production Server Stage
FROM nginx:1.27-alpine AS runner

# Remove default nginx assets
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled SPA bundle from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add curl for health check
RUN apk --no-cache add curl

HEALTHCHECK --interval=25s --timeout=4s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
