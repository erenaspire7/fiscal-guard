"""Database session management."""
from typing import Generator

from core.database.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, database_url: str):
        """Initialize database manager with connection URL."""
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
