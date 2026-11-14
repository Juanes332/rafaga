"""Insert-if-absent administrator seed (JOB-A01)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings
from app.repositories.users import user_repository as users
from app.security.password.password_hasher import hash_password


async def seed_admin(session: AsyncSession, settings: Settings) -> bool:
    """Insert the configured architect; never touch an existing user."""
    if not (settings.admin_email and settings.admin_password):
        return False
    email = settings.admin_email.strip().lower()
    if await users.find_user_by_email(session, email):
        return False
    await users.insert_user(session, email, hash_password(settings.admin_password), "architect")
    await session.commit()
    return True
