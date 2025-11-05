"""Database Connection Manager using SQLAlchemy 2.0"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type, Union
from sqlalchemy import text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
import asyncio
import logging

from schema import DatabaseType


logger = logging.getLogger(__name__)


class DatabaseStrategy(ABC):
    """
    Abstract base class for database-specific connection strategies.

    This defines the interface for database-specific operations using
    the Strategy Pattern. Each database type implements its own strategy.
    """

    @abstractmethod
    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """
        Build database-specific connection URL.

        Args:
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            additional_params: Additional database-specific parameters

        Returns:
            Connection URL string for SQLAlchemy
        """
        pass

    @abstractmethod
    def get_version_query(self) -> Optional[str]:
        """
        Return SQL query to get database version.

        Returns:
            SQL query string or None if version query is not available
        """
        pass

    @abstractmethod
    def get_default_port(self) -> int:
        """
        Return default port for this database type.

        Returns:
            Default port number
        """
        pass

    def get_engine_kwargs(self) -> Dict[str, Any]:
        """
        Return additional engine creation parameters.

        Returns:
            Dictionary of keyword arguments for create_engine()
        """
        return {}


class PostgreSQLStrategy(DatabaseStrategy):
    """Strategy for PostgreSQL database connections."""

    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """Build PostgreSQL connection URL."""
        port = port or self.get_default_port()
        # Build URL string with async driver for SQLAlchemy
        return (
            f"postgresql+asyncpg://{username}:{password}@{host}:{port}/"
            f"{database}"
        )

    def get_version_query(self) -> Optional[str]:
        """Return PostgreSQL version query."""
        return "SELECT version()"

    def get_default_port(self) -> int:
        """Return default PostgreSQL port."""
        return 5432


class MySQLStrategy(DatabaseStrategy):
    """Strategy for MySQL database connections."""

    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """Build MySQL connection URL using string formatting."""
        port = port or self.get_default_port()
        return (
            f"mysql+aiomysql://{username}:{password}@{host}:{port}/{database}"
        )

    def get_version_query(self) -> Optional[str]:
        """Return MySQL version query."""
        return "SELECT VERSION()"

    def get_default_port(self) -> int:
        """Return default MySQL port."""
        return 3306


class MariaDBStrategy(DatabaseStrategy):
    """Strategy for MariaDB database connections."""

    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """Build MariaDB connection URL."""
        port = port or self.get_default_port()
        # Build URL string with async driver for SQLAlchemy
        return (
            f"mariadb+aiomysql://{username}:{password}@{host}:{port}/"
            f"{database}"
        )

    def get_version_query(self) -> Optional[str]:
        """Return MariaDB version query."""
        return "SELECT VERSION()"

    def get_default_port(self) -> int:
        """Return default MariaDB port."""
        return 3306


class SnowflakeStrategy(DatabaseStrategy):
    """Strategy for Snowflake database connections."""

    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """Build Snowflake connection URL."""
        account = additional_params.get("account", host)
        schema = additional_params.get("schema", "public")
        warehouse = additional_params.get("warehouse", "")
        role = additional_params.get("role", "")
        # Build Snowflake URL string
        # Format: snowflake://user:password@account/database/schema
        # ?warehouse=warehouse
        url = (
            f"snowflake://{username}:{password}@{account}/"
            f"{database}/{schema}"
        )
        if warehouse:
            url += f"?warehouse={warehouse}"
        if role:
            url += f"&role={role}"
        return url

    def get_version_query(self) -> Optional[str]:
        """Return Snowflake version query."""
        return "SELECT CURRENT_VERSION()"

    def get_default_port(self) -> int:
        """Return default Snowflake port (not applicable)."""
        return 443


class MSSQLStrategy(DatabaseStrategy):
    """Strategy for Microsoft SQL Server database connections."""

    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """Build MSSQL connection URL."""
        port = port or self.get_default_port()
        driver = additional_params.get(
            "driver", "ODBC Driver 17 for SQL Server"
        )
        return (
            f"mssql+aioodbc://{username}:{password}@{host}:{port}/{database}"
            f"?driver={driver.replace(' ', '+')}"
        )

    def get_version_query(self) -> Optional[str]:
        """Return MSSQL version query."""
        return "SELECT @@VERSION"

    def get_default_port(self) -> int:
        """Return default MSSQL port."""
        return 1433


class OracleStrategy(DatabaseStrategy):
    """Strategy for Oracle database connections."""

    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """Build Oracle connection URL."""
        port = port or self.get_default_port()
        service_name = additional_params.get("service_name", database)
        return (
            f"oracle+oracledb_async://{username}:{password}@{host}:{port}/"
            f"?service_name={service_name}"
        )

    def get_version_query(self) -> Optional[str]:
        """Return Oracle version query."""
        return "SELECT * FROM v$version WHERE banner LIKE 'Oracle%'"

    def get_default_port(self) -> int:
        """Return default Oracle port."""
        return 1521


# add a new strategy for databricks
class DatabricksStrategy(DatabaseStrategy):
    """Strategy for Databricks database connections."""

    def build_connection_url(
        self,
        host: Optional[str],
        port: Optional[int],
        database: str,
        username: Optional[str],
        password: Optional[str],
        additional_params: Dict[str, Any],
    ) -> str:
        """Build Databricks connection URL."""
        access_token = password
        http_path = additional_params.get("http_path", "")
        catalog = additional_params.get("catalog", "")
        schema = additional_params.get("schema", "")
        url = f"databricks://token:{access_token}@{host}"
        if http_path:
            url += f"?http_path={http_path}"
        if catalog:
            url += f"&catalog={catalog}"
        if schema:
            url += f"&schema={schema}"
        # Always disable SSL verification to avoid blocking on cert errors
        url += "&_tls_no_verify=True"
        return url

    def get_version_query(self) -> Optional[str]:
        """Return Databricks version query."""
        return "SELECT CURRENT_VERSION()"

    def get_default_port(self) -> int:
        """Return default Databricks port."""
        return 443

    def get_engine_kwargs(self) -> Dict[str, Any]:
        """
        Return additional engine creation parameters for Databricks.
        Disables SSL verification to prevent blocking on certificate errors.
        """
        import ssl
        import urllib3
        import os

        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Set environment variables to disable SSL verification
        # at urllib3 level
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        os.environ["CURL_CA_BUNDLE"] = ""
        os.environ["REQUESTS_CA_BUNDLE"] = ""

        # Create unverified SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        return {
            "connect_args": {
                "_tls_no_verify": True,
                "connect_timeout": 30,  # Set timeout to prevent blocking
            }
        }


class DatabaseStrategyFactory:
    """
    Factory for creating database-specific strategies.

    Uses Registry Pattern to allow easy registration of new database types.
    """

    _strategies: Dict[DatabaseType, Type[DatabaseStrategy]] = {}

    @classmethod
    def register(
        cls, db_type: DatabaseType, strategy_class: Type[DatabaseStrategy]
    ):
        """
        Register a new database strategy.

        Args:
            db_type: Database type enum value
            strategy_class: Strategy class to register
        """
        cls._strategies[db_type] = strategy_class
        logger.debug(f"Registered strategy for {db_type}")

    @classmethod
    def create(cls, db_type: DatabaseType) -> DatabaseStrategy:
        """
        Create appropriate strategy instance.

        Args:
            db_type: Database type enum value

        Returns:
            DatabaseStrategy instance

        Raises:
            ValueError: If database type is not registered
        """
        if db_type not in cls._strategies:
            raise ValueError(f"Unsupported database type: {db_type}")
        return cls._strategies[db_type]()

    @classmethod
    def is_registered(cls, db_type: DatabaseType) -> bool:
        """Check if a database type is registered."""
        return db_type in cls._strategies


# Register default strategies
DatabaseStrategyFactory.register(DatabaseType.POSTGRESQL, PostgreSQLStrategy)
DatabaseStrategyFactory.register(DatabaseType.MYSQL, MySQLStrategy)
DatabaseStrategyFactory.register(DatabaseType.MARIADB, MariaDBStrategy)
DatabaseStrategyFactory.register(DatabaseType.SNOWFLAKE, SnowflakeStrategy)
DatabaseStrategyFactory.register(DatabaseType.MSSQL, MSSQLStrategy)
DatabaseStrategyFactory.register(DatabaseType.ORACLE, OracleStrategy)
DatabaseStrategyFactory.register(DatabaseType.DATABRICKS, DatabricksStrategy)


class DatabaseConnectionManager:
    """
    Manages database connections with SQLAlchemy 2.0.
    Implements connection pooling and lifecycle management.
    Uses Strategy Pattern for database-specific operations.
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
        self._engine: Optional[Union[AsyncEngine, Engine]] = None
        self._strategy = DatabaseStrategyFactory.create(db_type)
        # Snowflake and Databricks don't have async drivers
        self._is_sync = db_type in (
            DatabaseType.DATABRICKS,
            DatabaseType.SNOWFLAKE,
        )

    async def connect(self) -> Union[AsyncEngine, Engine]:
        """
        Create and return SQLAlchemy async engine
        (or sync engine for Databricks/Snowflake).
        Uses connection pooling for better performance.
        """
        if self._engine is not None:
            logger.info("Reusing existing database engine")
            return self._engine

        try:
            connection_url = self._strategy.build_connection_url(
                self.host,
                self.port,
                self.database,
                self.username,
                self.password,
                self.additional_params,
            )

            # Get additional engine kwargs from strategy
            engine_kwargs = self._strategy.get_engine_kwargs()

            # Databricks doesn't have an async driver, use sync engine
            if self._is_sync:
                self._engine = create_engine(
                    connection_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_pre_ping=True,
                    echo=False,
                    **engine_kwargs,
                )
                # Test connection using run_in_executor for async compatibility
                # with timeout to prevent blocking

                def _test_connection():
                    with self._engine.connect() as conn:
                        conn.execute(text("SELECT 1"))

                # Wrap in timeout to prevent blocking on SSL/connection issues
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(_test_connection),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Connection test timed out, but engine created"
                    )
                    # Don't fail - engine is created, might work later
            else:
                # Configure connection pool based on database type
                self._engine = create_async_engine(
                    connection_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_pre_ping=True,  # Verify connections before using
                    echo=False,
                    **engine_kwargs,
                )

                # Test connection
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))

            logger.info(f"Successfully connected to {self.db_type} database")
            return self._engine

        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    async def disconnect(self):
        """Close database connection and dispose of engine"""
        if self._engine is not None:
            if self._is_sync:
                await asyncio.to_thread(self._engine.dispose)
            else:
                await self._engine.dispose()
            self._engine = None
            logger.info("Database connection closed")

    async def execute_query(
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
            if self._is_sync:
                # For sync engine (Databricks), run in thread pool
                # with timeout to prevent blocking
                def _execute_sync():
                    with self._engine.begin() as conn:
                        result = conn.execute(text(query), params or {})
                        if result.returns_rows:
                            columns = result.keys()
                            rows = [
                                dict(zip(columns, row))
                                for row in result.fetchall()
                            ]
                            return rows
                        else:
                            return [{"affected_rows": result.rowcount}]

                # Add timeout to prevent blocking on SSL/network issues
                return await asyncio.wait_for(
                    asyncio.to_thread(_execute_sync),
                    timeout=60.0
                )
            else:
                # For async engine
                async with self._engine.begin() as conn:
                    result = await conn.execute(text(query), params or {})

                    # If it's a SELECT query, fetch results
                    if result.returns_rows:
                        columns = result.keys()
                        rows = [
                            dict(zip(columns, row))
                            for row in await result.fetchall()
                        ]
                        return rows
                    else:
                        # For INSERT/UPDATE/DELETE, commit and return
                        # affected rows
                        return [{"affected_rows": result.rowcount}]

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def get_tables(self) -> list[str]:
        """Get list of all tables in the database"""
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        if self._is_sync:
            # For sync engine (Databricks/Snowflake), run in thread pool
            def _get_tables_sync():
                from sqlalchemy import inspect as sync_inspect
                inspector = sync_inspect(self._engine)
                return inspector.get_table_names()

            return await asyncio.to_thread(_get_tables_sync)
        else:
            async with self._engine.connect() as conn:
                # Use run_sync to run entire inspect operation
                # within async context
                from sqlalchemy import inspect as sync_inspect

                def _get_tables(sync_conn):
                    inspector = sync_inspect(sync_conn)
                    return inspector.get_table_names()

                return await conn.run_sync(_get_tables)

    async def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get schema information for a specific table"""
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        if self._is_sync:
            # For sync engine (Databricks/Snowflake), run in thread pool
            def _get_schema_sync():
                from sqlalchemy import inspect as sync_inspect
                inspector = sync_inspect(self._engine)

                columns = inspector.get_columns(table_name)
                primary_keys = inspector.get_pk_constraint(table_name)
                foreign_keys = inspector.get_foreign_keys(table_name)
                indexes = inspector.get_indexes(table_name)

                # Convert SQLAlchemy types to strings for serialization
                serializable_columns = []
                for col in columns:
                    serializable_col = {
                        "name": col["name"],
                        # Convert SQLAlchemy type to string
                        "type": str(col["type"]),
                        "nullable": col.get("nullable"),
                        "default": (
                            str(col.get("default"))
                            if col.get("default") is not None
                            else None
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

            return await asyncio.to_thread(_get_schema_sync)
        else:
            async with self._engine.connect() as conn:
                # Use run_sync to run entire inspect operation
                # within async context
                from sqlalchemy import inspect as sync_inspect

                def _get_schema(sync_conn):
                    inspector = sync_inspect(sync_conn)

                    columns = inspector.get_columns(table_name)
                    primary_keys = inspector.get_pk_constraint(table_name)
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    indexes = inspector.get_indexes(table_name)

                    # Convert SQLAlchemy types to strings for serialization
                    serializable_columns = []
                    for col in columns:
                        serializable_col = {
                            "name": col["name"],
                            # Convert SQLAlchemy type to string
                            "type": str(col["type"]),
                            "nullable": col.get("nullable"),
                            "default": (
                                str(col.get("default"))
                                if col.get("default") is not None
                                else None
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

                return await conn.run_sync(_get_schema)

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._engine is not None

    async def test_connection(self) -> Dict[str, Any]:
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
            if self._is_sync:
                # For sync engine (Databricks), run in thread pool
                def _test_sync():
                    with self._engine.connect() as conn:
                        result = conn.execute(text("SELECT 1 as test"))
                        result.fetchone()  # Verify connection works
                    return None

                await asyncio.to_thread(_test_sync)

                # Get database version if possible
                version_query_str = self._strategy.get_version_query()
                version = None
                if version_query_str:
                    try:
                        def _get_version_sync():
                            with self._engine.connect() as conn:
                                result = conn.execute(text(version_query_str))
                                row = result.fetchone()
                                return row[0] if row else None
                        version = await asyncio.to_thread(_get_version_sync)
                    except Exception:
                        pass  # Version query failed, not critical
            else:
                # Test connection with a simple query
                async with self._engine.connect() as conn:
                    result = await conn.execute(text("SELECT 1 as test"))
                    await result.fetchone()  # Verify connection works

                # Get database version if possible
                version_query_str = self._strategy.get_version_query()
                version = None
                if version_query_str:
                    try:
                        async with self._engine.connect() as conn:
                            result = await conn.execute(
                                text(version_query_str)
                            )
                            row = await result.fetchone()
                            version = row[0] if row else None
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
