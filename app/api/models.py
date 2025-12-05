import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class MemberRole(enum.Enum):
    partner = "partner"
    admin = "admin"


class RelationshipType(enum.Enum):
    romantic = "romantic"
    friendship = "friendship"
    family = "family"


class RelationshipStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    ended = "ended"


class InviteStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    revoked = "revoked"
    expired = "expired"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    supabase_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )
    time_zone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(120), nullable=True)


class Relationship(Base):
    __tablename__ = "relationships"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[RelationshipType] = mapped_column(
        SAEnum(RelationshipType, name="relationship_type"),
        default=RelationshipType.romantic,
        nullable=False,
    )
    status: Mapped[RelationshipStatus] = mapped_column(
        SAEnum(RelationshipStatus, name="relationship_status"),
        default=RelationshipStatus.active,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )


class RelationshipMember(Base):
    __tablename__ = "relationship_members"
    __table_args__ = (
        UniqueConstraint("relationship_id", "user_id", name="uniq_relationship_member"),
        Index("index_rel_members_user_id", "user_id"),
        Index("index_rel_members_relationship_id", "relationship_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    relationship_id: Mapped[int] = mapped_column(
        ForeignKey("relationships.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[MemberRole] = mapped_column(
        SAEnum(MemberRole, name="member_role"), default=MemberRole.partner, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )


class Invite(Base):
    __tablename__ = "invites"
    __table_args__ = (
        Index(
            "ix_invites_unique_pending_per_relationship_email",
            "relationship_id",
            "invitee_email",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_invites_expires_at", "expires_at"),
        Index("ix_invites_invitee_email", "invitee_email"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    relationship_id: Mapped[int | None] = mapped_column(
        ForeignKey("relationships.id", ondelete="SET NULL"), nullable=True
    )
    inviter_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invitee_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invitee_email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[MemberRole] = mapped_column(
        SAEnum(MemberRole, name="member_role"), default=MemberRole.partner, nullable=False
    )
    inviter_email: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[InviteStatus] = mapped_column(
        SAEnum(InviteStatus, name="invite_status"),
        default=InviteStatus.pending,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )
