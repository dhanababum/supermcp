"""Database Connection Manager using SQLAlchemy 2.0"""

from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool
import logging

from schema import DatabaseType

from pydantic import (
    AnyUrl,
    MySQLDsn,
    PostgresDsn,
    MariaDBDsn,
    SnowflakeDsn,
    ClickHouseDsn,
)


logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """
    Manages database connections with SQLAlchemy 2.0.
    Implements connection pooling and lifecycle management.
    """

    def __init__(
        self,
        db_type: DatabaseType,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
    ):
        """
        Initialize database connection manager.

        Args:
            db_type: Type of database (sqlite, postgresql, mysql, etc.)
            host: Database host
            port: Database port
            database: Database name or file path (for SQLite)
            username: Database username
            password: Database password
            additional_params: Additional connection parameters
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Pool timeout in seconds
        """
        self.db_type = db_type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.additional_params = additional_params or {}
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self._engine: Optional[Engine] = None

    def _build_connection_url(self) -> str:
        """Build SQLAlchemy connection URL based on database type"""

        if self.db_type == DatabaseType.POSTGRESQL:
            # PostgreSQL: postgresql://user:password@host:port/database
            port = self.port or 5432
            url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            return url

        elif self.db_type == DatabaseType.MYSQL:
            # MySQL: mysql+pymysql://user:password@host:port/database
            port = self.port or 3306
            url = f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            return url
        
        elif self.db_type == DatabaseType.MARIADB:
            port = self.port or 3306
            url = MariaDBDsn(
                scheme="mariadb",
                user=self.username,
                password=self.password,
                host=self.host,
                port=port,
                path=f"/{self.database}",
            )
            return url
        
        elif self.db_type == DatabaseType.CLICKHOUSE:
            port = self.port or 9000
            url = ClickHouseDsn(
                scheme="clickhouse",
                user=self.username,
                password=self.password,
                host=self.host,
                port=port,
                path=f"/{self.database}",
            )
            return url
        
        elif self.db_type == DatabaseType.SNOWFLAKE:
            account = self.additional_params.get("account", self.host)
            schema = self.additional_params.get("schema", "public")
            url = SnowflakeDsn(
                scheme="snowflake",
                user=self.username,
                password=self.password,
                host=account,
                database=self.database,
                schema=schema,
            )
            return url
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def connect(self) -> Engine:
        """
        Create and return SQLAlchemy engine.
        Uses connection pooling for better performance.
        """
        if self._engine is not None:
            logger.info("Reusing existing database engine")
            return self._engine

        try:
            connection_url = self._build_connection_url()

            # Configure connection pool based on database type
            self._engine = create_engine(
                connection_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_pre_ping=True,  # Verify connections before using
                echo=False,
            )

            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(f"Successfully connected to {self.db_type} database")
            return self._engine

        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def disconnect(self):
        """Close database connection and dispose of engine"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            logger.info("Database connection closed")

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> list:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters (for parameterized queries)

        Returns:
            List of row dictionaries
        """
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})

                # If it's a SELECT query, fetch results
                if result.returns_rows:
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    return rows
                else:
                    # For INSERT/UPDATE/DELETE, commit and return affected rows
                    conn.commit()
                    return [{"affected_rows": result.rowcount}]

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def get_tables(self) -> list[str]:
        """Get list of all tables in the database"""
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        inspector = inspect(self._engine)
        return inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get schema information for a specific table"""
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        inspector = inspect(self._engine)

        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)

        # Convert SQLAlchemy types to strings for serialization
        serializable_columns = []
        for col in columns:
            serializable_col = {
                "name": col["name"],
                "type": str(col["type"]),  # Convert SQLAlchemy type to string
                "nullable": col.get("nullable"),
                "default": (
                    str(col.get("default")) if col.get("default") is not None else None
                ),
                "autoincrement": col.get("autoincrement"),
                "comment": col.get("comment"),
            }
            serializable_columns.append(serializable_col)

        return {
            "table_name": table_name,
            "columns": serializable_columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
        }

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._engine is not None

    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection and return connection information.
        
        Returns:
            Dictionary with connection status and database information
        """
        if self._engine is None:
            return {
                "status": "disconnected",
                "connected": False,
                "db_type": self.db_type.value,
                "error": "Database not connected"
            }
        
        try:
            # Test connection with a simple query
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
            
            # Get database version if possible
            version_query = None
            if self.db_type == DatabaseType.POSTGRESQL:
                version_query = text("SELECT version()")
            elif self.db_type == DatabaseType.MYSQL:
                version_query = text("SELECT VERSION()")
            elif self.db_type == DatabaseType.MSSQL:
                version_query = text("SELECT @@VERSION")
            elif self.db_type == DatabaseType.SNOWFLAKE:
                version_query = text("SELECT CURRENT_VERSION()")
            
            version = None
            if version_query:
                try:
                    with self._engine.connect() as conn:
                        result = conn.execute(version_query)
                        version = result.fetchone()[0]
                except Exception:
                    pass  # Version query failed, not critical
            
            return {
                "status": "connected",
                "connected": True,
                "db_type": self.db_type.value,
                "database": self.database,
                "host": self.host,
                "port": self.port,
                "version": version,
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "db_type": self.db_type.value,
                "error": str(e)
            }
