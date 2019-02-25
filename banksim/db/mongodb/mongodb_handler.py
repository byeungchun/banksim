import configparser

from pymongo import MongoClient
from pymongo.cursor import CursorType
from banksim.db.base_handler import DBHandler

class MongoDBHandler(DBHandler):
    """
    PyMongo wrapper
    local - local database, remote - remote database
    """
    def __init__(self, mode="local", db_name=None, collection_name=None):
        """
        MongoDBHandler __init__ 

        Args:
            mode (str): local or remove DB ex) local, remote
            db_name (str): 
            collection_name (str): 

        Returns:
            None

        Raises:
            throw an exception if db_name and collection_name don't exist
        """
        if db_name is None or collection_name is None:
            raise Exception("Need to db name and collection name")
        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        self.db_config = {}
        self.db_config["local_ip"] = config['MONGODB']['local_ip']
        self.db_config["port"] = config['MONGODB']['port']
        self.db_config["remote_host"] = config['MONGODB']['remote_host']
        self.db_config["remote_port"] = config['MONGODB']['remote_port']
        self.db_config["user"] = config['MONGODB']['user']
        self.db_config["password"] = config['MONGODB']['password']

        if mode == "remote":
            self._client = MongoClient("mongodb://{user}:{password}@{remote_host}:{remote_port}".format(**self.db_config))
        elif mode == "local":
            self._client = MongoClient("mongodb://{local_ip}:{port}".format(**self.db_config))

        self._db = self._client[db_name]
        self._collection = self._db[collection_name]

    def set_db_collection(self, db_name=None, collection_name=None):
        """
        To change database and collection working on MongoDB

        Args:
            db_name (str): 
            collection_name (str): 

        Returns:
            None

        Raises:
            Throw an exception if db_name doesn't exist
        """    
        if db_name is None:
            raise Exception("Need to dbname name")

        self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
            
    def get_current_db_name(self):
        """
        Return database name working in MongoDB
        
        Returns:
            self._db.name : 
        """
        return self._db.name

    def get_current_collection_name(self):
        """
        Return collection working in MongoDB
        
        Returns:
            self._collection.name : 
        """
        return self._collection.name

    def insert_item(self, data, db_name=None, collection_name=None):
        """
        To insert a document to MongoDB
        
        Args:
            db_name (str): 
            collection_name (str): 

        Returns:
            inserted_id : 
        """
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.insert_one(data).inserted_id

    def insert_items(self, datas, db_name=None, collection_name=None):
        """
        To insert documents to MongoDB
        
        Args:
            db_name (str):
            collection_name (str):

        Returns:
            inserted_ids :
        """
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection_name = self._db[collection_name]
        return self._collection.insert_many(datas).inserted_ids

    def find_items(self, condition=None, db_name=None, collection_name=None):
        """
        To search documents in MongoDB
        
        Args:
            condition (dict): search parameter
            db_name (str): 
            collection_name (str): 

        Returns:
            Cursor : 
        """
        if condition is None:
            condition = {}
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.find(condition, no_cursor_timeout=True, cursor_type=CursorType.EXHAUST)
    
    def find_item(self, condition=None, db_name=None, collection_name=None):
        """
        To search a document in MongoDB 
        
        Args:
            condition (dict): search parameter
            db_name (str): 
            collection_name (str): 

        Returns:
            document : 
        """
        if condition is None:
            condition = {}
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.find_one(condition)

    def delete_items(self, condition=None, db_name=None, collection_name=None):
        """
        To delete documents in MongoDB
        
        Args:
            condition (dict): 
            db_name (str): 
            collection_name (str): 

        Returns:
            DeleteResult : 
        """
        if condition is None:
            raise Exception("Need to condition")
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.delete_many(condition)

    def update_items(self, condition=None, update_value=None, db_name=None, collection_name=None):
        """
        To update documents in MongoDB
        
        Args:
            condition (dict): .
            update_value (dict) : 
            db_name (str): M
            collection_name (str): 

        Returns:
            UpdateResult : 
        """   
        if condition is None:
            raise Exception("Need to condition")
        if update_value is None:
            raise Exception("Need to update value")
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.update_many(filter=condition, update=update_value)

    def aggregate(self, pipeline=None, db_name=None, collection_name=None):
        """
        To aggregate values in collection
        
        Args:
            pipeline (dict): 
            db_name (str): 
            collection_name (str): 

        Returns:
            CommandCursor : CommandCursor returned
        """      
        if pipeline is None:
            raise Exception("Need to pipeline") 
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.aggregate(pipeline)
