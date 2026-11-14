# syntax=docker/dockerfile:1

# Resolved through nexcraft-conventions/runtimes.yaml: host Node 24 LTS meets the floor (>= 22).
ARG NODE_MAJOR=24

# ---- build ----
FROM node:${NODE_MAJOR}-slim AS build
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN npm install -g corepack && corepack enable
WORKDIR /app

# Manifests first so this layer only invalidates when dependencies change.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
# No VITE_API_URL: the API is discovered at runtime from /config.json (ADR-05).
RUN pnpm build

# ---- runtime ----
FROM node:${NODE_MAJOR}-slim AS runtime
RUN npm i -g serve@14
WORKDIR /app
# dist/ belongs to node so the entrypoint can write config.json without root.
COPY --from=build --chown=node:node /app/dist ./dist
COPY --chown=node:node serve.json ./dist/serve.json
COPY --chown=node:node docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
USER node
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD node -e "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# -s rewrites deep links to index.html; tcp://0.0.0.0 because serve binds to localhost by default.
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
