FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with increased memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm ci --silent || npm install --no-audit --no-fund --silent

# Copy all necessary config files
COPY index.html ./
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY jsconfig.json ./
COPY components.json ./

# Copy source code
COPY src ./src
COPY public ./public

# Ensure utils.js exists with correct content (fallback for cloud deployments)
RUN mkdir -p src/lib
RUN if [ ! -f src/lib/utils.js ]; then \
        echo 'import { clsx } from "clsx";' > src/lib/utils.js && \
        echo 'import { twMerge } from "tailwind-merge";' >> src/lib/utils.js && \
        echo '' >> src/lib/utils.js && \
        echo 'export function cn(...inputs) {' >> src/lib/utils.js && \
        echo '  return twMerge(clsx(inputs));' >> src/lib/utils.js && \
        echo '}' >> src/lib/utils.js; \
    fi

# Build with increased memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx config inline (more reliable than copying file)
RUN echo 'server {' > /etc/nginx/conf.d/default.conf && \
    echo '    listen 80;' >> /etc/nginx/conf.d/default.conf && \
    echo '    server_name _;' >> /etc/nginx/conf.d/default.conf && \
    echo '    root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    index index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    location / {' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '        add_header Content-Security-Policy "upgrade-insecure-requests" always;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '    location = /index.html {' >> /etc/nginx/conf.d/default.conf && \
    echo '        add_header Cache-Control "no-store" always;' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri =404;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '    location ~* \\.(?:js|css|png|jpg|jpeg|gif|svg|ico|woff2?)$ {' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri =404;' >> /etc/nginx/conf.d/default.conf && \
    echo '        expires 1y;' >> /etc/nginx/conf.d/default.conf && \
    echo '        add_header Cache-Control "public, immutable";' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '}' >> /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]


