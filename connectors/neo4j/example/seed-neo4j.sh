#!/bin/bash
# Script to seed Neo4j test database with sample data

set -e

NEO4J_HOST=${NEO4J_HOST:-localhost}
NEO4J_PORT=${NEO4J_PORT:-7687}
NEO4J_USER=${NEO4J_USER:-neo4j}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-testpassword123}

echo "Waiting for Neo4j to be ready..."
until curl -s http://${NEO4J_HOST}:7474 > /dev/null 2>&1; do
    echo "Neo4j not ready yet, waiting..."
    sleep 2
done

echo "Neo4j is ready. Loading seed data..."

# Use cypher-shell to load the data
cat init-data/seed-data.cypher | cypher-shell -a bolt://${NEO4J_HOST}:${NEO4J_PORT} -u ${NEO4J_USER} -p ${NEO4J_PASSWORD}

echo "Seed data loaded successfully!"
echo ""
echo "Test connection:"
echo "  URI: bolt://${NEO4J_HOST}:${NEO4J_PORT}"
echo "  Username: ${NEO4J_USER}"
echo "  Password: ${NEO4J_PASSWORD}"
echo "  Database: neo4j"
echo ""
echo "Sample queries to test:"
echo "  MATCH (n:Person) RETURN n.name LIMIT 5"
echo "  MATCH (m:Movie) RETURN m.title, m.released"
echo "  MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN p.name, m.title"
