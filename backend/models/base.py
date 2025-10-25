from datetime import datetime
from bson import ObjectId
from typing import Any, Dict, List, Optional, Union
import structlog
from ..utils.helpers import serialize_object, is_valid_object_id

logger = structlog.get_logger()

class BaseModel:
    def __init__(self, collection_name: str, db_manager):
        self.collection_name = collection_name
        self.collection = db_manager.get_collection(collection_name)
        self.db_manager = db_manager
    
    def create(self, data: Dict[str, Any]) -> str:
        """Create a new document"""
        try:
            data['created_at'] = datetime.utcnow()
            data['updated_at'] = datetime.utcnow()
            result = self.collection.insert_one(data)
            logger.info("Document created", collection=self.collection_name, id=str(result.inserted_id))
            return str(result.inserted_id)
        except Exception as e:
            logger.error("Failed to create document", collection=self.collection_name, error=str(e))
            raise
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            if not is_valid_object_id(id):
                return None
            return self.collection.find_one({'_id': ObjectId(id)})
        except Exception as e:
            logger.error("Failed to get document by ID", collection=self.collection_name, id=id, error=str(e))
            return None
    
    def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update document by ID"""
        try:
            if not is_valid_object_id(id):
                return False
            data['updated_at'] = datetime.utcnow()
            result = self.collection.update_one({'_id': ObjectId(id)}, {'$set': data})
            success = result.modified_count > 0
            if success:
                logger.info("Document updated", collection=self.collection_name, id=id)
            return success
        except Exception as e:
            logger.error("Failed to update document", collection=self.collection_name, id=id, error=str(e))
            return False
    
    def delete(self, id: str) -> bool:
        """Delete document by ID"""
        try:
            if not is_valid_object_id(id):
                return False
            result = self.collection.delete_one({'_id': ObjectId(id)})
            success = result.deleted_count > 0
            if success:
                logger.info("Document deleted", collection=self.collection_name, id=id)
            return success
        except Exception as e:
            logger.error("Failed to delete document", collection=self.collection_name, id=id, error=str(e))
            return False
    
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document by query"""
        try:
            return self.collection.find_one(query)
        except Exception as e:
            logger.error("Failed to find document", collection=self.collection_name, query=query, error=str(e))
            return None
    
    def find_many(self, query: Dict[str, Any] = None, sort: List[tuple] = None, 
                  limit: int = None, skip: int = None) -> List[Dict[str, Any]]:
        """Find multiple documents by query"""
        try:
            cursor = self.collection.find(query or {})
            
            if sort:
                cursor = cursor.sort(sort)
            
            if skip:
                cursor = cursor.skip(skip)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error("Failed to find documents", collection=self.collection_name, query=query, error=str(e))
            return []
    
    def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents by query"""
        try:
            return self.collection.count_documents(query or {})
        except Exception as e:
            logger.error("Failed to count documents", collection=self.collection_name, query=query, error=str(e))
            return 0
    
    def exists(self, query: Dict[str, Any]) -> bool:
        """Check if document exists"""
        try:
            return self.collection.count_documents(query, limit=1) > 0
        except Exception as e:
            logger.error("Failed to check document existence", collection=self.collection_name, query=query, error=str(e))
            return False
    
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """Create multiple documents"""
        try:
            now = datetime.utcnow()
            for data in data_list:
                data['created_at'] = now
                data['updated_at'] = now
            
            result = self.collection.insert_many(data_list)
            ids = [str(id) for id in result.inserted_ids]
            logger.info("Bulk documents created", collection=self.collection_name, count=len(ids))
            return ids
        except Exception as e:
            logger.error("Failed to bulk create documents", collection=self.collection_name, error=str(e))
            raise
    
    def bulk_update(self, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents"""
        try:
            if '$set' not in update:
                update['$set'] = {}
            update['$set']['updated_at'] = datetime.utcnow()
            result = self.collection.update_many(query, update)
            logger.info("Bulk documents updated", collection=self.collection_name, count=result.modified_count)
            return result.modified_count
        except Exception as e:
            logger.error("Failed to bulk update documents", collection=self.collection_name, error=str(e))
            return 0
    
    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline"""
        try:
            return list(self.collection.aggregate(pipeline))
        except Exception as e:
            logger.error("Failed to run aggregation", collection=self.collection_name, pipeline=pipeline, error=str(e))
            return []
    
    def create_index(self, keys: Union[str, List[tuple]], unique: bool = False, 
                    background: bool = True) -> str:
        """Create database index"""
        try:
            result = self.collection.create_index(keys, unique=unique, background=background)
            logger.info("Index created", collection=self.collection_name, index=result)
            return result
        except Exception as e:
            logger.error("Failed to create index", collection=self.collection_name, keys=keys, error=str(e))
            raise
    
    def drop_index(self, index_name: str) -> bool:
        """Drop database index"""
        try:
            self.collection.drop_index(index_name)
            logger.info("Index dropped", collection=self.collection_name, index=index_name)
            return True
        except Exception as e:
            logger.error("Failed to drop index", collection=self.collection_name, index=index_name, error=str(e))
            return False
    
    def serialize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize document for API response"""
        if not document:
            return None
        
        return serialize_object(document)
    
    def serialize_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Serialize multiple documents for API response"""
        return [self.serialize_document(doc) for doc in documents]