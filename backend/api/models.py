import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from database import LOCAL_USER, Base


class ThreatModel(Base):
    __tablename__ = "threat_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner = Column(String(255), nullable=False, index=True, default=LOCAL_USER)
    title = Column(String(512), nullable=True)
    diagram_path = Column(String(1024), nullable=True)
    application_type = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class JobStatus(Base):
    __tablename__ = "job_status"

    id = Column(
        UUID(as_uuid=True),
        ForeignKey("threat_models.id", ondelete="CASCADE"),
        primary_key=True,
    )
    state = Column(String(32), nullable=False, default="PENDING")
    detail = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threat_model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("threat_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(String(64), nullable=False)
    detail = Column(JSONB, nullable=True)
    source_ip = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
