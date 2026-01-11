# Database - SurrealDB

SurrealDB configuration for agent memory persistence.

## Quick Start

```bash
# Start SurrealDB
docker compose up -d surrealdb

# Apply migrations
docker compose --profile migrate up

# Load sample data (optional)
docker compose --profile seed up
```

## Schema

### Namespace & Database

- **Namespace**: `local_agent_memory`
- **Database**: `main_database`

### Tables

| Table | Description |
|-------|-------------|
| `agno_sessions` | Chat sessions |
| `agno_memories` | Agent memories |
| `agno_session_summaries` | Session summaries |
| `agno_knowledge_content` | Knowledge base entries |
| `agno_knowledge_vector` | Embedding vectors (HNSW index) |

## Structure

```
database/
├── migrations/
│   └── schema.surql    # Schema definitions
└── seeds/
    └── data.surql      # Sample data
```

## Direct Access

### SurrealDB CLI

```bash
surreal sql \
  --endpoint http://localhost:8000 \
  --username root \
  --password root \
  --namespace local_agent_memory \
  --database main_database
```

### Example Queries

```sql
-- List all sessions
SELECT * FROM agno_sessions;

-- Get memories for a user
SELECT * FROM agno_memories WHERE user_id = 'user123';

-- Search knowledge base
SELECT * FROM agno_knowledge_content
WHERE content CONTAINS 'search term';
```

## Backup & Restore

### Backup

```bash
surreal export \
  --endpoint http://localhost:8000 \
  --username root \
  --password root \
  --namespace local_agent_memory \
  --database main_database \
  backup.surql
```

### Restore

```bash
surreal import \
  --endpoint http://localhost:8000 \
  --username root \
  --password root \
  --namespace local_agent_memory \
  --database main_database \
  backup.surql
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SURREALDB_USERNAME` | `root` | Database user |
| `SURREALDB_PASSWORD` | `root` | Database password |
| `SURREALDB_PORT` | `8000` | Database port |
| `SURREALDB_NAMESPACE` | `local_agent_memory` | Namespace |
| `SURREALDB_DATABASE` | `main_database` | Database name |
| `SURREALDB_VERSION` | `v2` | SurrealDB version |

## Web Interface

Access the SurrealDB web interface at http://localhost:8000

Credentials: `root` / `root` (default)
