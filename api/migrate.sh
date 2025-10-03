#!/bin/bash

# Alembic Migration Helper Script
# Makes running migrations easier

set -e

cd "$(dirname "$0")"

case "$1" in
  "upgrade")
    echo "📈 Upgrading database to latest migration..."
    uv run alembic upgrade head
    echo "✅ Database upgraded successfully!"
    ;;
    
  "downgrade")
    echo "📉 Downgrading database by 1 version..."
    uv run alembic downgrade -1
    echo "✅ Database downgraded successfully!"
    ;;
    
  "create")
    if [ -z "$2" ]; then
      echo "❌ Error: Please provide a migration message"
      echo "Usage: ./migrate.sh create 'Add new field'"
      exit 1
    fi
    echo "🔨 Creating new migration: $2"
    uv run alembic revision --autogenerate -m "$2"
    echo "✅ Migration created! Review the file in alembic/versions/"
    ;;
    
  "current")
    echo "📍 Current database version:"
    uv run alembic current
    ;;
    
  "history")
    echo "📜 Migration history:"
    uv run alembic history --verbose
    ;;
    
  "reset")
    echo "⚠️  WARNING: This will downgrade to base (empty database)"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      echo "📉 Downgrading to base..."
      uv run alembic downgrade base
      echo "✅ Database reset to base!"
    else
      echo "❌ Reset cancelled"
    fi
    ;;
    
  "status")
    echo "📊 Migration Status:"
    echo ""
    echo "Current Version:"
    uv run alembic current
    echo ""
    echo "Available Migrations:"
    uv run alembic history
    ;;
    
  *)
    echo "Alembic Migration Helper"
    echo ""
    echo "Usage: ./migrate.sh <command>"
    echo ""
    echo "Commands:"
    echo "  upgrade         - Apply all pending migrations"
    echo "  downgrade       - Rollback last migration"
    echo "  create <msg>    - Create new migration with message"
    echo "  current         - Show current database version"
    echo "  history         - Show migration history"
    echo "  status          - Show migration status"
    echo "  reset           - Downgrade to base (WARNING: removes all tables)"
    echo ""
    echo "Examples:"
    echo "  ./migrate.sh upgrade"
    echo "  ./migrate.sh create 'Add email field'"
    echo "  ./migrate.sh current"
    ;;
esac

