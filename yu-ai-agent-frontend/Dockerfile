# =============================================================================
# Yu AI Agent Frontend - Multi-stage Docker Build
# =============================================================================
# Stage 1: Build stage
FROM node:20-alpine AS builder

# 设置 npm 使用淘宝镜像源
RUN npm config set registry https://registry.npmmirror.com

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Build for production
RUN npm run build


# Stage 2: Production stage
FROM nginx:alpine AS production

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
