"""
GroupController - handle document group operations
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.DocumentGroup import DocumentGroup
from src.domain.repositories.DocumentGroupRepository import DocumentGroupRepository
from src.infrastructure.database.postgres.connection import get_db
from src.infrastructure.database.postgres.models import UserModel
from src.infrastructure.http.dependencies import get_document_group_repository
from src.infrastructure.security.auth import get_current_user

router = APIRouter(prefix="/api/groups", tags=["Groups"])


class GroupCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None  # Hex color like "#3B82F6"


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class GroupResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, group: DocumentGroup) -> "GroupResponse":
        return cls(
            id=group.id,
            user_id=group.user_id,
            name=group.name,
            description=group.description,
            color=group.color,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: GroupCreateRequest,
    group_repository: DocumentGroupRepository = Depends(get_document_group_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new document group"""
    now = datetime.now(timezone.utc)
    group = DocumentGroup(
        id="",  # Will be generated
        user_id=str(current_user.id),
        name=request.name,
        description=request.description,
        color=request.color,
        created_at=now,
        updated_at=now,
    )
    
    created_group = await group_repository.create(group)
    return GroupResponse.from_entity(created_group)


@router.get("", response_model=List[GroupResponse])
async def list_groups(
    group_repository: DocumentGroupRepository = Depends(get_document_group_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """List all groups for current user"""
    groups = await group_repository.get_by_user_id(str(current_user.id))
    return [GroupResponse.from_entity(group) for group in groups]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    group_repository: DocumentGroupRepository = Depends(get_document_group_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a specific group"""
    group = await group_repository.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this group"
        )
    
    return GroupResponse.from_entity(group)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    request: GroupUpdateRequest,
    group_repository: DocumentGroupRepository = Depends(get_document_group_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Update a document group"""
    group = await group_repository.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this group"
        )
    
    # Update fields
    if request.name is not None:
        group.name = request.name
    if request.description is not None:
        group.description = request.description
    if request.color is not None:
        group.color = request.color
    group.updated_at = datetime.now(timezone.utc)
    
    updated_group = await group_repository.update(group)
    return GroupResponse.from_entity(updated_group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    group_repository: DocumentGroupRepository = Depends(get_document_group_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a document group (documents will have group_id set to NULL)"""
    group = await group_repository.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this group"
        )
    
    await group_repository.delete(group_id)

