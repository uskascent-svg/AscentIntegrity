import enum, uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
def utcnow(): return datetime.now(timezone.utc)
class UserRole(str, enum.Enum):
    admin="admin"
    analyst="analyst"
    viewer="viewer"
class User(Base):
    __tablename__="users"
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    email: Mapped[str]=mapped_column(String(320),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[UserRole]=mapped_column(Enum(UserRole),default=UserRole.analyst)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class Evidence(Base):
    __tablename__="evidence"
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    case_reference: Mapped[str]=mapped_column(String(100),index=True)
    filename: Mapped[str]=mapped_column(String(255))
    media_type: Mapped[str]=mapped_column(String(150),default="application/octet-stream")
    byte_size: Mapped[int]=mapped_column(BigInteger)
    sha256: Mapped[str]=mapped_column(String(64),index=True)
    storage_key: Mapped[str]=mapped_column(String(80),unique=True)
    uploaded_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    status: Mapped[str]=mapped_column(String(24),default="stored")
class EvidenceVersion(Base):
    __tablename__="evidence_versions"
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    evidence_id: Mapped[str]=mapped_column(ForeignKey("evidence.id"),index=True)
    version_number: Mapped[int]=mapped_column()
    sha256: Mapped[str]=mapped_column(String(64))
    byte_size: Mapped[int]=mapped_column(BigInteger)
    storage_key: Mapped[str]=mapped_column(String(80),unique=True)
    created_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class AuditEvent(Base):
    __tablename__="audit_events"
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    actor_id: Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True)
    action: Mapped[str]=mapped_column(String(100),index=True)
    resource_type: Mapped[str]=mapped_column(String(80))
    resource_id: Mapped[str|None]=mapped_column(String(36),nullable=True)
    detail: Mapped[str]=mapped_column(Text,default="{}")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class BlockchainAnchor(Base):
    __tablename__="blockchain_anchors"
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    evidence_id: Mapped[str]=mapped_column(ForeignKey("evidence.id"),index=True)
    sha256: Mapped[str]=mapped_column(String(64))
    status: Mapped[str]=mapped_column(String(24),default="not_configured")
    tx_hash: Mapped[str|None]=mapped_column(String(80),nullable=True)
    block_number: Mapped[int|None]=mapped_column(nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
