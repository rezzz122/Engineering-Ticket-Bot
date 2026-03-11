from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TicketMapping(Base):
    __tablename__ = "ticket_mappings"

    jira_key: Mapped[str] = mapped_column(String, primary_key=True)
    pylon_ticket_id: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
