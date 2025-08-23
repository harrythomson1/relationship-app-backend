from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Example(Base):
    __tablename__ = "examples"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
