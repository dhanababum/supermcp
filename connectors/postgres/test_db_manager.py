"""
Test suite for PoolManager class in db_manager.py

Run with: uv run pytest test_db_manager.py -v
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from connectors.postgres.db_manager import PoolManager
from connectors.postgres.schema import PostgresConfig


@pytest.fixture
def sample_config():
    """Create a sample PostgreSQL configuration for testing"""
    return PostgresConfig(
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_password",
        pool_size=5,
        max_overflow=10
    )


@pytest.fixture
def pool_manager():
    """Create a PoolManager instance for testing"""
    return PoolManager(
        global_max_connections=100,
        per_target_max=10,
        idle_ttl=300
    )


class TestPoolManagerInitialization:
    """Test PoolManager initialization"""

    def test_pool_manager_initialization(self):
        """Test that PoolManager initializes with correct default values"""
        pm = PoolManager()
        assert pm.global_max == 500
        assert pm.per_target_max == 20
        assert pm.idle_ttl == 300
        assert pm.total_connections == 0
        assert len(pm.pools) == 0
        assert pm._is_sync is True

    def test_pool_manager_custom_values(self):
        """Test PoolManager initialization with custom values"""
        pm = PoolManager(
            global_max_connections=100,
            per_target_max=5,
            idle_ttl=600
        )
        assert pm.global_max == 100
        assert pm.per_target_max == 5
        assert pm.idle_ttl == 600


class TestPoolCreation:
    """Test pool creation and management"""

    @pytest.mark.asyncio
    async def test_create_pool(self, pool_manager, sample_config):
        """Test creating a new pool"""
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool) as mock_create:
            pool = await pool_manager._create_pool(sample_config)
            
            assert pool == mock_pool
            # Check that create_pool was called with correct base parameters
            call_args = mock_create.call_args[1]  # Get keyword arguments
            assert call_args['user'] == sample_config.username
            assert call_args['password'] == sample_config.password
            assert call_args['database'] == sample_config.database
            assert call_args['host'] == sample_config.host
            assert call_args['port'] == sample_config.port
            assert call_args['min_size'] == 0
            assert call_args['max_size'] == 5

    @pytest.mark.asyncio
    async def test_get_pool_creates_new(self, pool_manager, sample_config):
        """Test get_pool creates a new pool when one doesn't exist"""
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            pool = await pool_manager.get_pool("server1", sample_config)
            
            assert pool == mock_pool
            assert "server1" in pool_manager.pools
            assert pool_manager.total_connections == 5

    @pytest.mark.asyncio
    async def test_get_pool_reuses_existing(self, pool_manager, sample_config):
        """Test get_pool reuses an existing pool"""
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            # Get pool first time
            pool1 = await pool_manager.get_pool("server1", sample_config)
            
            # Get pool second time - should reuse
            pool2 = await pool_manager.get_pool("server1", sample_config)
            
            assert pool1 == pool2
            assert pool_manager.total_connections == 5  # Same connection count

    @pytest.mark.asyncio
    async def test_get_pool_enforces_global_limit(self, sample_config):
        """Test that get_pool enforces global connection limits"""
        pm = PoolManager(
            global_max_connections=10,
            per_target_max=6,  # Changed to 6 so 6 + 6 = 12 > 10
            idle_ttl=300
        )
        
        mock_pool1 = AsyncMock()
        mock_pool1._maxsize = 6
        mock_pool1.close = AsyncMock()
        
        mock_pool2 = AsyncMock()
        mock_pool2._maxsize = 6
        
        async def create_pool_side_effect(*args, **kwargs):
            if not hasattr(create_pool_side_effect, 'call_count'):
                create_pool_side_effect.call_count = 0
            create_pool_side_effect.call_count += 1
            return mock_pool1 if create_pool_side_effect.call_count == 1 else mock_pool2
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   side_effect=create_pool_side_effect):
            # Create first pool
            await pm.get_pool("server1", sample_config)
            assert pm.total_connections == 6
            
            # Create second pool - should evict first one since 6 + 6 > 10
            await pm.get_pool("server2", sample_config)
            assert pm.total_connections == 6
            assert "server1" not in pm.pools
            assert "server2" in pm.pools
            mock_pool1.close.assert_called_once()


class TestPoolEviction:
    """Test pool eviction logic"""

    @pytest.mark.asyncio
    async def test_evict_one(self, pool_manager, sample_config):
        """Test evicting a single pool"""
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.close = AsyncMock()
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            await pool_manager.get_pool("server1", sample_config)
            assert pool_manager.total_connections == 5
            
            await pool_manager.evict_one()
            assert pool_manager.total_connections == 0
            assert "server1" not in pool_manager.pools
            mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_pool(self, pool_manager, sample_config):
        """Test closing a specific pool"""
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.close = AsyncMock()
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            await pool_manager.get_pool("server1", sample_config)
            
            result = await pool_manager.close_pool("server1")
            assert result is True
            assert "server1" not in pool_manager.pools
            assert pool_manager.total_connections == 0
            mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_nonexistent_pool(self, pool_manager):
        """Test closing a pool that doesn't exist"""
        result = await pool_manager.close_pool("nonexistent")
        assert result is False


class TestQueryExecution:
    """Test query execution functionality"""

    @pytest.mark.asyncio
    async def test_execute_query_select(self, pool_manager, sample_config):
        """Test executing a SELECT query"""
        # Create mock dict-like objects that behave like asyncpg.Record
        class MockRecord(dict):
            pass
        
        mock_record1 = MockRecord({'id': 1, 'name': 'test1'})
        mock_record2 = MockRecord({'id': 2, 'name': 'test2'})
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_record1, mock_record2])
        
        # Create async context manager for acquire()
        mock_acquire = AsyncMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.acquire = MagicMock(return_value=mock_acquire)
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            result = await pool_manager.execute_query(
                "server1",
                sample_config,
                "SELECT * FROM test_table"
            )
            
            assert len(result) == 2
            assert result[0] == {'id': 1, 'name': 'test1'}
            assert result[1] == {'id': 2, 'name': 'test2'}

    @pytest.mark.asyncio
    async def test_execute_query_insert(self, pool_manager, sample_config):
        """Test executing an INSERT query"""
        mock_conn = AsyncMock()
        # asyncpg execute returns a string like "INSERT 0 1"
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")
        
        # Create async context manager for acquire()
        mock_acquire = AsyncMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.acquire = MagicMock(return_value=mock_acquire)
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            result = await pool_manager.execute_query(
                "server1",
                sample_config,
                "INSERT INTO test_table VALUES (1, 'test')"
            )
            
            assert result == [{"affected_rows": 1}]

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, pool_manager, sample_config):
        """Test executing a query with parameters"""
        # Create mock dict-like object
        class MockRecord(dict):
            pass
        
        mock_record = MockRecord({'id': 1})
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_record])
        
        # Create async context manager for acquire()
        mock_acquire = AsyncMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.acquire = MagicMock(return_value=mock_acquire)
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            result = await pool_manager.execute_query(
                "server1",
                sample_config,
                "SELECT * FROM test_table WHERE id = $1",
                params={'id': 1}
            )
            
            assert len(result) == 1
            assert result[0]['id'] == 1

    @pytest.mark.asyncio
    async def test_execute_query_error(self, pool_manager, sample_config):
        """Test query execution with error"""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Database error"))
        
        # Create async context manager for acquire()
        mock_acquire = AsyncMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.acquire = MagicMock(return_value=mock_acquire)
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            with pytest.raises(Exception) as exc_info:
                await pool_manager.execute_query(
                    "server1",
                    sample_config,
                    "INVALID SQL"
                )
            
            assert "Database error" in str(exc_info.value)


class TestSchemaOperations:
    """Test schema inspection operations"""

    @pytest.mark.asyncio
    async def test_get_tables(self, pool_manager, sample_config):
        """Test getting list of tables"""
        # Create mock Records for table names
        mock_records = [
            {'table_name': 'table1'},
            {'table_name': 'table2'},
            {'table_name': 'table3'}
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=mock_records)
        
        # Create async context manager for acquire()
        mock_acquire = AsyncMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.acquire = MagicMock(return_value=mock_acquire)
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            result = await pool_manager.get_tables("server1", sample_config)
            
            assert result == ['table1', 'table2', 'table3']
            mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_table_schema(self, pool_manager, sample_config):
        """Test getting table schema"""
        # Mock column information
        mock_col_records = [
            {
                'column_name': 'id',
                'data_type': 'integer',
                'is_nullable': 'NO',
                'column_default': 'nextval(\'test_table_id_seq\'::regclass)',
                'character_maximum_length': None
            }
        ]
        
        # Mock primary key information
        mock_pk_records = [{'attname': 'id'}]
        
        # Mock foreign keys and indexes (empty)
        mock_fk_records = []
        mock_idx_records = []
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=[
            mock_col_records,
            mock_pk_records,
            mock_fk_records,
            mock_idx_records
        ])
        
        # Create async context manager for acquire()
        mock_acquire = AsyncMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.acquire = MagicMock(return_value=mock_acquire)
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            result = await pool_manager.get_table_schema(
                "server1",
                sample_config,
                "test_table"
            )
            
            assert result['table_name'] == 'test_table'
            assert len(result['columns']) == 1
            assert result['columns'][0]['name'] == 'id'
            assert result['columns'][0]['type'] == 'integer'
            assert result['primary_keys'] == {'constrained_columns': ['id']}


class TestCleanupLoop:
    """Test cleanup loop functionality"""

    @pytest.mark.asyncio
    async def test_cleanup_loop_evicts_idle_pools(self, sample_config):
        """Test that cleanup loop evicts idle pools"""
        pm = PoolManager(
            global_max_connections=100,
            per_target_max=10,
            idle_ttl=0.5  # 0.5 seconds for faster testing
        )
        
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        mock_pool.close = AsyncMock()
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            # Create a pool
            await pm.get_pool("server1", sample_config)
            assert "server1" in pm.pools
            
            # Wait for TTL to expire
            await asyncio.sleep(0.6)
            
            # Run one iteration of cleanup
            async with pm.lock:
                now = asyncio.get_event_loop().time()
                for key, (pool, last_used, maxsize, _) in list(pm.pools.items()):
                    if now - last_used > pm.idle_ttl:
                        await pool.close()
                        pm.total_connections -= maxsize
                        del pm.pools[key]
            
            # Pool should be evicted
            assert "server1" not in pm.pools
            mock_pool.close.assert_called_once()


class TestConcurrency:
    """Test concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_pool_access(self, pool_manager, sample_config):
        """Test that multiple concurrent requests work correctly"""
        mock_pool = AsyncMock()
        mock_pool._maxsize = 5
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   new_callable=AsyncMock, return_value=mock_pool):
            # Create multiple concurrent requests
            tasks = [
                pool_manager.get_pool("server1", sample_config)
                for _ in range(10)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should get the same pool
            assert all(pool == mock_pool for pool in results)
            assert "server1" in pool_manager.pools

    @pytest.mark.asyncio
    async def test_concurrent_pool_creation(self, pool_manager, sample_config):
        """Test creating multiple pools concurrently"""
        mock_pools = [AsyncMock() for _ in range(3)]
        for i, mock_pool in enumerate(mock_pools):
            mock_pool._maxsize = 5
        
        async def create_pool_multi(*args, **kwargs):
            if not hasattr(create_pool_multi, 'call_count'):
                create_pool_multi.call_count = 0
            idx = create_pool_multi.call_count
            create_pool_multi.call_count += 1
            return mock_pools[idx] if idx < len(mock_pools) else mock_pools[-1]
        
        with patch('connectors.postgres.db_manager.asyncpg.create_pool', 
                   side_effect=create_pool_multi):
            # Create pools for different servers concurrently
            tasks = [
                pool_manager.get_pool(f"server{i}", sample_config)
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Should have 3 different pools
            assert len(results) == 3
            assert pool_manager.total_connections == 15  # 3 pools * 5 connections


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

