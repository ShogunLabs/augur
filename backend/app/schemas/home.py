from pydantic import BaseModel

from app.schemas.ipo import IPOListItem


class HomeResponse(BaseModel):
    upcoming: list[IPOListItem]
    open: list[IPOListItem]
    closed: list[IPOListItem]
    listed: list[IPOListItem]