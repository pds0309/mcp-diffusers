# MCP Diffusers

## Start

**set env**

```
cp env.template .env
vi .env
```

**docker compose up**

```
docker network create mcp-diffusers
docker compose -f docker-compose.storage.yml up -d
docker compose -f docker-compose.zimage.yml up -d
```

