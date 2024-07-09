# Dojo
One API to rule them all, One API to find them, One API to bring them all and in the AI-Dojo bind them.

## Deployments for different usages

### Simulation only (optional)
(if you don't want to build whole docker compose)
```shell
docker run --detach --publish 127.0.0.1:8000:8000 registry.gitlab.ics.muni.cz:443/ai-dojo/dojo
```

### Simulation and Emulation
```shell
docker compose up -d --build
```

### Development
```shell
docker compose -f docker-compose.yml -f docker-compose-dev.yml up -d
```

Access the API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)