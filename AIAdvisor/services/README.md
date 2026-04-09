# Services

Shared Solr instances used by skill tests and evals.

Each subdirectory is a named instance with:
- **Setup**: `docker-compose.yml` or `setup.sh` to start the service
- **Health check**: `verify.py` — run with `pytest verify.py -v` to confirm the service is up and loaded

## Instances

| Name | Port | Description |
|------|------|-------------|
| `techproducts` | 38983 | SolrCloud 8 + ZK with TechProducts sample data |
| `tmdb` | 38984 | Solr 8 with ~10K TMDB movie documents (text-heavy) |

## Usage

```bash
# TechProducts
cd techproducts && docker compose up -d
pytest verify.py -v
docker compose down -v

# TMDB
cd tmdb && bash setup.sh
pytest verify.py -v
bash setup.sh teardown
```
