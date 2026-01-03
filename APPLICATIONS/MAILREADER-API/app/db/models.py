import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)

    # UI’dan seçilecek: exchange | imap
    auth_method: Mapped[str] = mapped_column(String(32), default="imap")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    secret = relationship("Secret", back_populates="account", uselist=False, cascade="all, delete-orphan")
    rules = relationship("Rule", back_populates="account", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="account", cascade="all, delete-orphan")


class Secret(Base):
    __tablename__ = "secrets"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True
    )
    enc_payload: Mapped[str] = mapped_column(Text)  # encrypted JSON payload
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="secret")


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True
    )

    name: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(default=True)
    priority: Mapped[int] = mapped_column(Integer, default=50)

    # [{"field":"subject","op":"icontains","value":"invoice"}]
    conditions: Mapped[dict] = mapped_column(JSONB, default=list)

    # {"set_category":"important"}
    action: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="rules")


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

    # IMAP Message-ID
    message_id: Mapped[str] = mapped_column(String(512), index=True)

    from_addr: Mapped[str] = mapped_column(String(512))
    to_addr: Mapped[str] = mapped_column(String(512))

    subject: Mapped[str] = mapped_column(String(1024))

    # FINAL CATEGORY (rule veya AI sonucu)
    category: Mapped[str] = mapped_column(String(32))  # important | normal | spam

    # === VAR OLAN ALANLAR (SİLİNMEDİ) ===
    confidence: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(256))

    # === AI EKLEMELERİ (YENİ) ===
    ai_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Rule adı (eşleştiyse)
    matched_rule: Mapped[str | None] = mapped_column(String(128), nullable=True)

    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    account = relationship("Account", back_populates="emails")

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "message_id",
            name="uq_email_account_message"
        ),
    )
