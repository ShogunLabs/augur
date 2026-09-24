from sqlalchemy.orm import Session

from app.repositories.home import get_home_sections
from app.services.ipo import serialize_ipo_list


def get_home(
    db: Session,
    limit: int = 10,
):
    sections = get_home_sections(
        db=db,
        limit=limit,
    )

    return {
        section: [
            serialize_ipo_list(ipo)
            for ipo in items
        ]
        for section, items in sections.items()
    }