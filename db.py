import os

from dotenv import load_dotenv
load_dotenv()

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class _Database():
    def __init__(self):
        self._user = os.getenv("DB_USER")
        self._pass = os.getenv("DB_PASS")
        self._name = os.getenv("DB_NAME")
        self._uri = f"mongodb+srv://{self._user}:{self._pass}@mongo-cluster.wjtgqic.mongodb.net/{self._name}?retryWrites=true&w=majority&appName=Mongo-Cluster"
        self._client = MongoClient(self._uri, server_api=ServerApi("1"))
    
    def get_db(self):
        return self._client.get_database(self._name)
        
database = _Database().get_db()