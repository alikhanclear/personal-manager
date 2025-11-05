"""
Database Connector Module for CasualHero BI Platform

Manages PostgreSQL database connections for both AWS and Neon databases.
Supports connection pooling, SSL, and error handling for production environments.

Migration Strategy:
    - Phase 1 (MVP): Connect to AWS PostgreSQL materialized view
    - Phase 2: Reverse engineer view logic
    - Phase 3: Migrate to Neon Serverless PostgreSQL

Features:
    - SQLAlchemy connection management
    - Connection pooling (configurable)
    - SSL/TLS support (required for AWS RDS and Neon)
    - Automatic reconnection handling
    - Environment variable configuration
    - Context managers for safe transactions
    - Works with both AWS RDS and Neon (same code, different URL)

Configuration:
    Set DATABASE_URL environment variable:

    # AWS PostgreSQL (Phase 1)
    DATABASE_URL=postgresql://user:pass@aws-host:5432/dbname

    # Neon PostgreSQL (Phase 3)
    DATABASE_URL=postgresql://user:pass@neon-host:5432/dbname
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.exc import SQLAlchemyError


# ============================================================================
# Configuration
# ============================================================================

class DatabaseConfig:
    """Database configuration from environment variables."""

    def __init__(self):
        # Try DATABASE_URL first (full connection string) - PREFERRED
        self.database_url = os.getenv('DATABASE_URL')

        # If not provided, build from individual components
        if not self.database_url:
            self.host = os.getenv('DB_HOST', 'localhost')
            self.port = int(os.getenv('DB_PORT', '5432'))
            self.database = os.getenv('DB_NAME', 'casualhero')
            self.user = os.getenv('DB_USER', 'postgres')
            self.password = os.getenv('DB_PASSWORD', '')

            # Build connection string
            password_encoded = quote_plus(self.password) if self.password else ''
            self.database_url = (
                f"postgresql://{self.user}:{password_encoded}@"
                f"{self.host}:{self.port}/{self.database}"
            )

        # Connection pool settings
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # 1 hour

        # SSL settings (required for AWS RDS and Neon)
        self.ssl_enabled = os.getenv('DB_SSL_ENABLED', 'true').lower() == 'true'
        self.ssl_mode = os.getenv('DB_SSL_MODE', 'require')  # require, verify-ca, verify-full

    def get_connection_args(self) -> dict:
        """
        Get connection arguments for SQLAlchemy engine.

        Returns:
            Dictionary of connection arguments including SSL settings
        """
        connect_args = {}

        if self.ssl_enabled:
            connect_args['sslmode'] = self.ssl_mode

        return connect_args


# ============================================================================
# Database Engine
# ============================================================================

class DatabaseConnector:
    """
    Database connection manager using SQLAlchemy.

    Provides connection pooling, SSL support, and error handling
    for PostgreSQL database operations. Works with both AWS RDS
    and Neon Serverless PostgreSQL.

    Example:
        >>> db = DatabaseConnector()
        >>> db.connect()
        >>> with db.get_session() as session:
        ...     result = session.execute(text("SELECT 1"))
        >>> db.close()
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database connector.

        Args:
            config: DatabaseConfig instance (creates default if None)
        """
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def connect(self) -> Engine:
        """
        Create database engine with connection pooling.

        Returns:
            SQLAlchemy Engine instance

        Raises:
            SQLAlchemyError: If connection fails
        """
        if self._engine is not None:
            return self._engine

        try:
            # Create engine with connection pooling
            self._engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,  # Verify connections before using
                connect_args=self.config.get_connection_args(),
                echo=False,  # Set to True for SQL query logging
            )

            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)

            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            return self._engine

        except SQLAlchemyError as e:
            raise SQLAlchemyError(
                f"Failed to connect to database: {e}\n"
                f"Check DATABASE_URL or DB_* environment variables.\n"
                f"For AWS: Ensure security group allows connections.\n"
                f"For Neon: Ensure SSL is enabled (sslmode=require)."
            ) from e

    def get_engine(self) -> Engine:
        """
        Get or create database engine.

        Returns:
            SQLAlchemy Engine instance
        """
        if self._engine is None:
            self.connect()
        return self._engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Automatically commits on success, rolls back on error,
        and closes the session when done.

        Yields:
            SQLAlchemy Session instance

        Example:
            >>> db = DatabaseConnector()
            >>> with db.get_session() as session:
            ...     result = session.execute(text("SELECT * FROM materialized_view"))
            ...     # Session auto-commits and closes
        """
        if self._session_factory is None:
            self.connect()

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @contextmanager
    def get_connection(self) -> Generator:
        """
        Context manager for raw database connections.

        Use this for executing raw SQL without ORM overhead.
        Preferred for read-only queries from materialized views.

        Yields:
            SQLAlchemy Connection instance

        Example:
            >>> db = DatabaseConnector()
            >>> with db.get_connection() as conn:
            ...     result = conn.execute(text("SELECT * FROM orders_view"))
        """
        engine = self.get_engine()
        connection = engine.connect()
        try:
            yield connection
        finally:
            connection.close()

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise

        Example:
            >>> db = DatabaseConnector()
            >>> if db.test_connection():
            ...     print("Connected!")
        """
        try:
            with self.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def close(self) -> None:
        """
        Close all database connections and dispose engine.

        Call this when shutting down the application.
        """
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# ============================================================================
# Global Connector Instance
# ============================================================================

# Singleton instance for application-wide use
_db_connector: Optional[DatabaseConnector] = None


def get_db() -> DatabaseConnector:
    """
    Get or create global database connector instance.

    Returns:
        DatabaseConnector singleton instance

    Example:
        >>> from src.data.connector import get_db
        >>> db = get_db()
        >>> with db.get_session() as session:
        ...     result = session.execute(text("SELECT * FROM orders"))
    """
    global _db_connector
    if _db_connector is None:
        _db_connector = DatabaseConnector()
        _db_connector.connect()
    return _db_connector


def close_db() -> None:
    """Close global database connector."""
    global _db_connector
    if _db_connector is not None:
        _db_connector.close()
        _db_connector = None


# ============================================================================
# Utility Functions
# ============================================================================

def execute_query(query: str, params: Optional[dict] = None) -> list:
    """
    Execute a raw SQL query and return results.

    Args:
        query: SQL query string (use :param_name for parameters)
        params: Dictionary of query parameters

    Returns:
        List of result rows (as dicts)

    Example:
        >>> # Query AWS materialized view
        >>> results = execute_query(
        ...     "SELECT * FROM orders_mv WHERE fiscal_year = :year",
        ...     {"year": 2024}
        ... )
    """
    db = get_db()
    with db.get_connection() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    print("Database Connector Module - Connection Test")
    print("=" * 60)

    # Load environment variables from .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded .env file")
    except ImportError:
        print("python-dotenv not installed, using environment variables")

    # Show configuration (mask password)
    config = DatabaseConfig()
    masked_url = config.database_url
    if '@' in masked_url:
        parts = masked_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            masked_url = f"{user_pass[0]}:***@{parts[1]}"

    print(f"\nDatabase Configuration:")
    print(f"  URL: {masked_url}")
    print(f"  Pool Size: {config.pool_size}")
    print(f"  Max Overflow: {config.max_overflow}")
    print(f"  SSL Enabled: {config.ssl_enabled}")
    print(f"  SSL Mode: {config.ssl_mode}")

    # Test connection
    print("\n" + "=" * 60)
    print("Testing Database Connection...")
    print("=" * 60)

    try:
        db = DatabaseConnector(config)
        if db.test_connection():
            print("SUCCESS: Database connection established!")

            # Test query
            with db.get_connection() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"\nPostgreSQL Version:")
                print(f"  {version[:80]}...")

                # Show database info
                result = conn.execute(text("SELECT current_database(), current_user"))
                db_name, user = result.fetchone()
                print(f"\nConnected to:")
                print(f"  Database: {db_name}")
                print(f"  User: {user}")

        else:
            print("FAILED: Could not connect to database")
            print("\nTroubleshooting:")
            print("  1. Check DATABASE_URL environment variable")
            print("  2. For AWS: Verify security group allows your IP")
            print("  3. For Neon: Ensure sslmode=require in connection string")
            print("  4. Verify credentials (username/password)")

    except Exception as e:
        print(f"ERROR: {e}")
        print("\nConnection failed. Common issues:")
        print("  - DATABASE_URL not set or invalid format")
        print("  - Network/firewall blocking connection")
        print("  - Invalid credentials")
        print("  - SSL required but not configured")

    finally:
        if 'db' in locals():
            db.close()
            print("\nConnection closed.")

    print("=" * 60)
