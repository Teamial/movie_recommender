FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies with increased memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm ci --silent || npm install --no-audit --no-fund --silent

# Copy source code (only frontend files)
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html ./
COPY frontend/vite.config.js ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/components.json ./
COPY frontend/jsconfig.json ./
COPY frontend/eslint.config.js ./

# Debug: Check if utils.js exists
RUN ls -la /app/src/lib/ || echo "lib directory not found"
RUN find /app -name "utils*" || echo "utils files not found"

# Build with increased memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]


