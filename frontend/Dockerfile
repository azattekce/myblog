# syntax=docker/dockerfile:1.7
# ---- 1) build: bağımlılıklar kilit dosyasından, testler + tip kontrolü build'in parçası --
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG RUN_TESTS=true
RUN if [ "$RUN_TESTS" = "true" ]; then npm run typecheck && npm run test; fi
RUN npm run build

# ---- 2) runtime: root olmayan nginx, yalnızca statik dosyalar -------------------
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime
USER root
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx/spa.conf /etc/nginx/conf.d/spa.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
