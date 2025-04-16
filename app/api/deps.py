from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db as get_db_dependency

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    """
    async with get_db_dependency() as db:
        yield db