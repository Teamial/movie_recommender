FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies with increased memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm ci --silent || npm install --no-audit --no-fund --silent

# Copy source code (only essential files)
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html ./

# Create vite config inline
RUN echo 'import path from "path"' > vite.config.js && \
    echo 'import { defineConfig } from "vite"' >> vite.config.js && \
    echo 'import react from "@vitejs/plugin-react"' >> vite.config.js && \
    echo '' >> vite.config.js && \
    echo 'export default defineConfig({' >> vite.config.js && \
    echo '  plugins: [react()],' >> vite.config.js && \
    echo '  resolve: {' >> vite.config.js && \
    echo '    alias: {' >> vite.config.js && \
    echo '      "@": path.resolve(__dirname, "./src"),' >> vite.config.js && \
    echo '    },' >> vite.config.js && \
    echo '  },' >> vite.config.js && \
    echo '})' >> vite.config.js

# Create minimal tailwind config inline
RUN echo '/** @type {import("tailwindcss").Config} */' > tailwind.config.js && \
    echo 'export default {' >> tailwind.config.js && \
    echo '  darkMode: ["class"],' >> tailwind.config.js && \
    echo '  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],' >> tailwind.config.js && \
    echo '  theme: {' >> tailwind.config.js && \
    echo '    extend: {' >> tailwind.config.js && \
    echo '      colors: {' >> tailwind.config.js && \
    echo '        background: "hsl(var(--background))",' >> tailwind.config.js && \
    echo '        foreground: "hsl(var(--foreground))",' >> tailwind.config.js && \
    echo '        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },' >> tailwind.config.js && \
    echo '        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },' >> tailwind.config.js && \
    echo '        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },' >> tailwind.config.js && \
    echo '        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },' >> tailwind.config.js && \
    echo '        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },' >> tailwind.config.js && \
    echo '        border: "hsl(var(--border))",' >> tailwind.config.js && \
    echo '        input: "hsl(var(--input))",' >> tailwind.config.js && \
    echo '        ring: "hsl(var(--ring))"' >> tailwind.config.js && \
    echo '      }' >> tailwind.config.js && \
    echo '    }' >> tailwind.config.js && \
    echo '  },' >> tailwind.config.js && \
    echo '  plugins: [require("tailwindcss-animate")]' >> tailwind.config.js && \
    echo '}' >> tailwind.config.js

# Create minimal postcss config inline
RUN echo 'module.exports = {' > postcss.config.js && \
    echo '  plugins: {' >> postcss.config.js && \
    echo '    tailwindcss: {},' >> postcss.config.js && \
    echo '    autoprefixer: {},' >> postcss.config.js && \
    echo '  },' >> postcss.config.js && \
    echo '}' >> postcss.config.js

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


