#==========================THIS CODES CREATED BY EIGHT
#==========================DB MODELS
#==========================LIBRARIES
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

#==========================BASE
class Base(DeclarativeBase):
    pass

#==========================ACCOUNTS TABLE
class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    auth_method: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    secret = relationship("Secret", back_populates="account", uselist=False)
    rules = relationship("Rule", back_populates="account")


#==========================SECRETS TABLE
class Secret(Base):
    __tablename__ = "secrets"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True
    )
    enc_payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    account = relationship("Account", back_populates="secret")


#==========================RULES TABLE
class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True
    )

    name: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(default=True)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    conditions: Mapped[dict] = mapped_column(JSONB)
    action: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    account = relationship("Account", back_populates="rules")


#==========================EMAILS TABLE
class Email(Base):
    __tablename__ = "emails"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True
    )

    message_id: Mapped[str] = mapped_column(String(512))
    from_addr: Mapped[str] = mapped_column(String(512))
    to_addr: Mapped[str] = mapped_column(String(512))
    subject: Mapped[str] = mapped_column(String(1024))

    category: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(256))

    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        index=True
    )
