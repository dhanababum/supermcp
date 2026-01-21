# Neo4j Graph Database Connector

MCP connector for Neo4j graph databases.

## Test Database Setup

Start a local Neo4j instance with sample movie data:

```bash
# Start Neo4j container
docker compose -f docker-compose.test.yml up -d

# Wait for Neo4j to be ready (~30s) then seed data
python seed_data.py
```

### Connection Details

| Parameter | Value |
|-----------|-------|
| URI | `bolt://localhost:7687` |
| Username | `neo4j` |
| Password | `testpassword123` |
| Database | `neo4j` |
| Browser | http://localhost:7474 |

### Sample Data

The test database contains a movie dataset:

**Nodes:**
- `Person` - Actors and directors (15 nodes)
- `Movie` - Films (8 nodes)
- `Studio` - Production studios (3 nodes)
- `Genre` - Movie genres (4 nodes)
- `Review` - Movie reviews (4 nodes)

**Relationships:**
- `ACTED_IN` - Actor to movie with role info
- `DIRECTED` - Director to movie
- `PRODUCED_BY` - Movie to studio
- `BELONGS_TO` - Movie to genre
- `KNOWS` - Person to person
- `REVIEWS` - Review to movie

### Sample Queries

```cypher
-- Get all actors
MATCH (p:Person {occupation: 'Actor'}) RETURN p.name

-- Find movies by actor
MATCH (p:Person {name: 'Keanu Reeves'})-[:ACTED_IN]->(m:Movie)
RETURN m.title, m.released

-- Get movie cast
MATCH (p:Person)-[r:ACTED_IN]->(m:Movie {title: 'The Matrix'})
RETURN p.name, r.role ORDER BY r.billing

-- Find co-actors
MATCH (p1:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(p2:Person)
WHERE p1.name = 'Leonardo DiCaprio' AND p1 <> p2
RETURN DISTINCT p2.name

-- Movies by genre
MATCH (m:Movie)-[:BELONGS_TO]->(g:Genre {name: 'Sci-Fi'})
RETURN m.title, m.released ORDER BY m.released
```

### Cleanup

```bash
docker compose -f docker-compose.test.yml down -v
```

## Configuration

| Field | Description | Default |
|-------|-------------|---------|
| `uri` | Neo4j connection URI | - |
| `username` | Authentication username | - |
| `password` | Authentication password | - |
| `database` | Database name | `neo4j` |
| `read_only` | Disable write operations | `false` |

## Tools

- `get_neo4j_schema` - Get database schema (labels, relationships, properties)
- `read_neo4j_cypher` - Execute read-only Cypher queries
- `write_neo4j_cypher` - Execute write Cypher queries (disabled in read-only mode)
- `test_connection` - Test database connectivity
