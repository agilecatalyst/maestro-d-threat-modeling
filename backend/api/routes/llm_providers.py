from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    LlmProviderProfileRequest,
    LlmProviderProfileResponse,
    LlmProviderTestResponse,
    LlmRoleBindingRequest,
    ResolvedProviderConfigResponse,
)
from security import require_internal_key
from services import llm_provider_service as service

router = APIRouter(prefix="/admin/llm-providers", tags=["llm-providers"])


@router.get("", response_model=list[LlmProviderProfileResponse])
def list_profiles(db: Session = Depends(get_db)):
    return service.list_profiles(db)


@router.post("", response_model=LlmProviderProfileResponse, status_code=201, dependencies=[Depends(require_internal_key)])
def create_profile(body: LlmProviderProfileRequest, db: Session = Depends(get_db)):
    return service.create_profile(db, body.model_dump())


@router.get("/roles")
def get_roles(db: Session = Depends(get_db)):
    return service.get_role_bindings(db)


@router.put("/roles/{role}", response_model=LlmProviderProfileResponse, dependencies=[Depends(require_internal_key)])
def set_role(role: str, body: LlmRoleBindingRequest, db: Session = Depends(get_db)):
    return service.set_role_binding(db, role, body.profile_id)


@router.get("/resolved/{role}", response_model=ResolvedProviderConfigResponse)
def get_resolved(role: str, db: Session = Depends(get_db)):
    return service.resolve(db, role)


@router.put("/{profile_id}", response_model=LlmProviderProfileResponse, dependencies=[Depends(require_internal_key)])
def update_profile(profile_id: UUID, body: LlmProviderProfileRequest, db: Session = Depends(get_db)):
    return service.update_profile(db, profile_id, body.model_dump())


@router.delete("/{profile_id}", status_code=204, dependencies=[Depends(require_internal_key)])
def delete_profile(profile_id: UUID, db: Session = Depends(get_db)):
    service.delete_profile(db, profile_id)
    return None


@router.post("/{profile_id}/test", response_model=LlmProviderTestResponse, dependencies=[Depends(require_internal_key)])
def test_profile(profile_id: UUID, db: Session = Depends(get_db)):
    return service.test_profile(db, profile_id)
