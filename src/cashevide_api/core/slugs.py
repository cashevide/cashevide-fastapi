import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

SLUG_MAX_LENGTH = 50


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


async def generate_unique_slug(
    db: AsyncSession, model, source_text: str, fallback: str
) -> str:

    base = slugify(source_text) or fallback
    number = 0

    while True:
        suffix = f"-{number}" if number else ""
        candidate = base[: SLUG_MAX_LENGTH - len(suffix)].rstrip("_-") + suffix

        taken = await db.scalar(select(model.id).where(model.slug == candidate))

        if taken is None:
            return candidate

        number += 1
