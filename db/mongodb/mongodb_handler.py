from pymongo import MongoClient
from pymongo.cursor import CursorType
import configparser
from autotrading.db.base_handler import DBHandler

class MongoDBHandler(DBHandler):
    """
    PyMongo를 Wrapping해서 사용하는 클래스입니다. DBHandler 추상화 클래스를 받습니다.
    Remote DB와 Local DB를 모두 사용할 수 있도록 __init__에서 mode로 구분합니다.
    
    """
    def __init__(self, mode="local", db_name=None, collection_name=None):
        """
        MongoDBHandler __init__ 구현부 .

        Args:
            mode (str): local DB인지 remote DB인지 구분합니다. ex) local, remote
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            None

        Raises:
            db_name과 collection_name이 없으면 Exception을 발생시킵니다.
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
        MongoDB에서 작업하려는 database와 collection을 변경할때 사용합니다.

        Args:
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            None

        Raises:
            db_name이 없으면 Exception을 발생시킵니다.
        """    
        if db_name is None:
            raise Exception("Need to dbname name")

        self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
            
    def get_current_db_name(self):
        """
        현재 MongoDB에서 작업 중인 database의 이름을 반환합니다.
        
        Returns:
            self._db.name : 현재 사용중인 database 이름을 반환
        """
        return self._db.name

    def get_current_collection_name(self):
        """
        현재 MongoDB에서 작업 중인 collection의 이름을 반환합니다.
        
        Returns:
            self._collection.name : 현재 사용중인 collection 이름을 반환
        """
        return self._collection.name

    def insert_item(self, data, db_name=None, collection_name=None):
        """
        MongoDB에 하나의 document를 입력하기 위한 메소드입니다.
        
        Args:
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            inserted_id : 입력 완료된 문서의 ObjectId를 반환합니다. 
        """
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.insert_one(data).inserted_id

    def insert_items(self, datas, db_name=None, collection_name=None):
        """
        MongoDB에 다수의 document를 입력하기 위한 메소드입니다.
        
        Args:
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            inserted_ids : 입력 완료된 문서의 ObjectId list를 반환합니다. 
        """
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection_name = self._db[collection_name]
        return self._collection.insert_many(datas).inserted_ids

    def find_items(self, condition=None, db_name=None, collection_name=None):
        """
        MongoDB에 다수의 document를 검색하기 위한 몌소드입니다. 
        
        Args:
            condition (dict): 검색 조건을 dictionary 형태로 받습니다.
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            Cursor : Cursor를 반환합니다.
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
        MongoDB에 하나의 document를 검색하기 위한 몌소드입니다. 
        
        Args:
            condition (dict): 검색 조건을 dictionary 형태로 받습니다.
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            document : 만약 검색된 문서가 있으면 문서의 내용을 반환합니다.
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
        MongoDB에 다수의 document를 삭제하기 위한 몌소드입니다. 
        
        Args:
            condition (dict): 삭제 조건을 dictionary 형태로 받습니다.
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            DeleteResult : PyMongo의 문서의 삭제 결과 객체 DeleteResult가 반환됩니다.
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
        MongoDB에 다수의 document를 갱신하기 위한 몌소드입니다. 
        
        Args:
            condition (dict): 갱신 조건을 dictionary 형태로 받습니다.
            update_value (dict) : 깽신하고자 하는 값을 dictionary 형태로 받습니다.
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            UpdateResult : PyMongo의 문서의 갱신 결과 객체 UpdateResult가 반환됩니다.
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
        MongoDB의 aggregate 작업을 위한 메소드 입니다.  
        
        Args:
            pipeline (dict): 갱신 조건을 dictionary 형태로 받습니다.
            db_name (str): MongoDB에서 database에 해당하는 이름을 받습니다.
            collection_name (str): database에 속하는 collection 이름을 받습니다.

        Returns:
            CommandCursor : PyMongo의 CommandCursor가 반환됩니다.
        """      
        if pipeline is None:
            raise Exception("Need to pipeline") 
        if db_name is not None:
            self._db = self._client[db_name]
        if collection_name is not None:
            self._collection = self._db[collection_name]
        return self._collection.aggregate(pipeline)
