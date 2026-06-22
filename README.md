# PetsFirst mock API

Local HTTP server that mimics the PetsFirst MCP REST API (`/api/v1.0/mcp/...`) for development and tests. No Django, agent, or MCP services in this repo.

## Run locally

```bash
pip install -r requirements.txt
python3 -m mock_backend
```

Health: `GET http://127.0.0.1:8020/health`

## Docker

```bash
make up.d    # or: docker compose up --build -d
make logs
make down
```

## Configuration

| Variable | Default |
|----------|---------|
| `MOCK_API_PORT` | `8020` |
| `MOCK_API_PREFIX` | `/api/v1.0/mcp` |

## Test phones

- **Registered:** `923001234567`, `971500000000` (user id 893, sample pets/clinics)
- **Unregistered:** numbers starting with `99999`

Edit `mock_backend/fixtures.py` and `mock_backend/state.py` to change responses and write behavior.

## Tests

```bash
make test
```
