from pymongo import MongoClient


class MongoHelper:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_db(self, db_name):
        connection_string = f"mongodb+srv://{self.username}:{self.password}@aarryamaan-cluster.emhtm8r.mongodb.net/{db_name}?retryWrites=true&w=majority&appName=Aarryamaan-Cluster"
        client = MongoClient(connection_string)
        db = client[db_name]
        return db

    def get_collection(self, db_name, collection_name):
        db = self.get_db(db_name)
        collection = db[collection_name]
        return collection
