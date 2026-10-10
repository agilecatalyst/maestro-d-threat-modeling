import uuid

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
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


class LlmProviderProfile(Base):
    __tablename__ = "llm_provider_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, unique=True)
    kind = Column(String(32), nullable=False)
    base_url = Column(String(512), nullable=True)
    model = Column(String(256), nullable=False)
    api_key_env = Column(String(128), nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    timeout_sec = Column(Integer, nullable=False, default=180)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class LlmRoleBinding(Base):
    __tablename__ = "llm_role_bindings"

    role = Column(String(32), primary_key=True)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llm_provider_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
