# API del control plane

## Endpoints mínimos

```text
POST   /campaigns
GET    /campaigns/{id}
POST   /campaigns/{id}/start
POST   /campaigns/{id}/pause
POST   /campaigns/{id}/resume
GET    /campaigns/{id}/leaderboard
GET    /campaigns/{id}/generations
GET    /strategies/{id}
GET    /strategies/{id}/lineage
POST   /strategies/import
POST   /strategies/{id}/canonical-backtest
GET    /experiments/{id}
GET    /experiments/{id}/artifacts
GET    /workers
GET    /health
```

## Eventos WebSocket

- campaign.progress
- generation.completed
- experiment.completed
- candidate.new_leader
- worker.failed
- checkpoint.saved
