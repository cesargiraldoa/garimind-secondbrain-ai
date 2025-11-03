def is_async_url(url: str) -> bool:
    return url.startswith("sqlite+aiosqlite") or url.startswith("postgresql+asyncpg")
