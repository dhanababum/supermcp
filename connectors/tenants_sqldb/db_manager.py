"""Database Connection Manager using SQLAlchemy 2.0"""
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool
import logging

from schema import DatabaseType

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
        
        if self.db_type == DatabaseType.SQLITE:
            # SQLite: sqlite:///path/to/database.db or sqlite:///:memory:
            return f"sqlite:///{self.database}"
        
        elif self.db_type == DatabaseType.POSTGRESQL:
            # PostgreSQL: postgresql://user:password@host:port/database
            port = self.port or 5432
            url = f"postgresql://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
            return url
        
        elif self.db_type == DatabaseType.MYSQL:
            # MySQL: mysql+pymysql://user:password@host:port/database
            port = self.port or 3306
            driver = self.additional_params.get("driver", "pymysql")
            url = f"mysql+{driver}://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
            return url
        
        elif self.db_type == DatabaseType.MSSQL:
            # MSSQL: mssql+pyodbc://user:password@host:port/database?driver=...
            port = self.port or 1433
            driver = self.additional_params.get("driver", "ODBC Driver 17 for SQL Server")
            url = f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
            if driver:
                url += f"?driver={driver}"
            return url
        
        elif self.db_type == DatabaseType.ORACLE:
            # Oracle: oracle+cx_oracle://user:password@host:port/?service_name=database
            port = self.port or 1521
            service_name = self.additional_params.get("service_name", self.database)
            url = f"oracle+cx_oracle://{self.username}:{self.password}@{self.host}:{port}/?service_name={service_name}"
            return url
        
        elif self.db_type == DatabaseType.SNOWFLAKE:
            # Snowflake: snowflake://user:password@account/database/schema?warehouse=warehouse
            account = self.additional_params.get("account", self.host)
            warehouse = self.additional_params.get("warehouse", "")
            schema = self.additional_params.get("schema", "public")
            url = f"snowflake://{self.username}:{self.password}@{account}/{self.database}/{schema}"
            if warehouse:
                url += f"?warehouse={warehouse}"
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
            if self.db_type == DatabaseType.SQLITE:
                # SQLite doesn't support connection pooling well
                self._engine = create_engine(
                    connection_url,
                    poolclass=NullPool,
                    echo=False,
                )
            else:
                # Use QueuePool for other databases
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
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> list:
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
        
        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
        }
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._engine is not None
