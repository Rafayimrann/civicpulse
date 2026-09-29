# STAGE 1: Build static assets using Node
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# STAGE 2: Serve static files using Nginx as non-root user
FROM nginx:1.30.5-alpine3.24-slim AS final

# Copy built static files and custom Nginx config
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Give the non-root 'nginx' user access to necessary directories
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx

# Switch to non-root user
USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
