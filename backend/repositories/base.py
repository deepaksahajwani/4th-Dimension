"""
Base Repository - Common database operations
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timezone
import logging

from utils.database import get_database

logger = logging.getLogger(__name__)
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, collection_name: str):
        self.db = get_database()
        self.collection_name = collection_name
        self.collection = self.db[collection_name]
    
    async def find_by_id(self, id: str, projection: Optional[Dict] = None) -> Optional[Dict]:
        """Find document by ID"""
        proj = projection or {}
        proj["_id"] = 0
        return await self.collection.find_one({"id": id}, proj)
    
    async def find_one(self, query: Dict, projection: Optional[Dict] = None) -> Optional[Dict]:
        """Find single document matching query"""
        proj = projection or {}
        proj["_id"] = 0
        return await self.collection.find_one(query, proj)
    
    async def find_many(
        self,
        query: Dict = None,
        projection: Optional[Dict] = None,
        sort: Optional[List] = None,
        limit: int = 1000,
        skip: int = 0
    ) -> List[Dict]:
        """Find multiple documents"""
        query = query or {}
        proj = projection or {}
        proj["_id"] = 0
        
        cursor = self.collection.find(query, proj)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        return await cursor.to_list(limit)
    
    async def insert(self, document: Dict) -> str:
        """Insert document and return ID"""
        if "created_at" not in document:
            document["created_at"] = datetime.now(timezone.utc).isoformat()
        if "updated_at" not in document:
            document["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.collection.insert_one(document)
        return document.get("id")
    
    async def update_by_id(self, id: str, update: Dict) -> bool:
        """Update document by ID"""
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await self.collection.update_one(
            {"id": id},
            {"$set": update}
        )
        return result.modified_count > 0
    
    async def update_one(self, query: Dict, update: Dict) -> bool:
        """Update single document matching query"""
        if "$set" in update:
            update["$set"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        else:
            update["updated_at"] = datetime.now(timezone.utc).isoformat()
            update = {"$set": update}
        
        result = await self.collection.update_one(query, update)
        return result.modified_count > 0
    
    async def delete_by_id(self, id: str, soft: bool = True) -> bool:
        """Delete document by ID (soft delete by default)"""
        if soft:
            return await self.update_by_id(id, {"deleted_at": datetime.now(timezone.utc).isoformat()})
        else:
            result = await self.collection.delete_one({"id": id})
            return result.deleted_count > 0
    
    async def count(self, query: Dict = None) -> int:
        """Count documents matching query"""
        return await self.collection.count_documents(query or {})
    
    async def exists(self, query: Dict) -> bool:
        """Check if document exists"""
        return await self.collection.find_one(query, {"_id": 1}) is not None
