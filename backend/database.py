from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, app=None):
        self.mongo = None
        self.db = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        try:
            self.mongo = PyMongo(app)
            self.db = self.mongo.db
            self.client = self.mongo.cx
            self.client.admin.command('ping')
            logger.info("MongoDB connected")
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    def get_collection(self, collection_name):
        return self.db[collection_name]

db_manager = DatabaseManager()