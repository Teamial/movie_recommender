FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
# Prefer npm ci, but fall back to npm install if lockfile is out of sync
RUN npm ci || npm install --no-audit --no-fund
COPY frontend ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


