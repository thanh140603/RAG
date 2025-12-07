"""
DocumentGroupRepository Implementation - Infrastructure Layer
Single Responsibility: Implement document group persistence using SQLAlchemy
"""
from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.DocumentGroup import DocumentGroup
from src.domain.repositories.DocumentGroupRepository import DocumentGroupRepository
from src.infrastructure.database.postgres.models import DocumentGroupModel
from src.infrastructure.database.postgres.mappers import DocumentGroupMapper


class DocumentGroupRepositoryImpl(DocumentGroupRepository):
    """
    SQLAlchemy implementation of DocumentGroupRepository
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, group: DocumentGroup) -> DocumentGroup:
        """Create a new document group"""
        model = DocumentGroupMapper.to_model(group)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return DocumentGroupMapper.to_entity(model)
    
    async def get_by_id(self, group_id: str) -> Optional[DocumentGroup]:
        """Get group by ID"""
        try:
            group_uuid = uuid.UUID(group_id) if group_id else None
            if not group_uuid:
                return None
            stmt = select(DocumentGroupModel).where(DocumentGroupModel.id == group_uuid)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            return DocumentGroupMapper.to_entity(model) if model else None
        except (ValueError, AttributeError):
            return None
    
    async def get_by_user_id(self, user_id: str) -> List[DocumentGroup]:
        """Get all groups for a user"""
        try:
            user_uuid = uuid.UUID(user_id) if user_id else None
            if not user_uuid:
                return []
            stmt = select(DocumentGroupModel).where(
                DocumentGroupModel.user_id == user_uuid
            ).order_by(DocumentGroupModel.created_at.desc())
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            return [DocumentGroupMapper.to_entity(model) for model in models]
        except (ValueError, AttributeError):
            return []
    
    async def update(self, group: DocumentGroup) -> DocumentGroup:
        """Update a document group"""
        try:
            group_uuid = uuid.UUID(group.id) if group.id else None
            if not group_uuid:
                raise ValueError(f"Invalid group ID: {group.id}")
            stmt = select(DocumentGroupModel).where(DocumentGroupModel.id == group_uuid)
            result = await self._session.execute(stmt)
            model = result.scalar_one()
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid group ID: {group.id}") from e
        
        model.name = group.name
        model.description = group.description
        model.color = group.color
        model.updated_at = group.updated_at
        
        await self._session.flush()
        await self._session.refresh(model)
        return DocumentGroupMapper.to_entity(model)
    
    async def delete(self, group_id: str) -> bool:
        """Delete a document group"""
        try:
            group_uuid = uuid.UUID(group_id) if group_id else None
            if not group_uuid:
                return False
            stmt = select(DocumentGroupModel).where(DocumentGroupModel.id == group_uuid)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                await self._session.delete(model)
                await self._session.flush()
                return True
            return False
        except (ValueError, AttributeError):
            return False
    
    async def exists(self, group_id: str) -> bool:
        """Check if group exists"""
        try:
            group_uuid = uuid.UUID(group_id) if group_id else None
            if not group_uuid:
                return False
            stmt = select(DocumentGroupModel).where(DocumentGroupModel.id == group_uuid)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except (ValueError, AttributeError):
            return False

