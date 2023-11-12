from pymongo import MongoClient

clientname = "mongo"
# clientname = "localhost"
dbname = "cse312"

class OurDataBase:
    def __init__(self, client_name=clientname, db_name=dbname):
        self.clientname = client_name
        self.dbname = db_name
        self.mongo_client = MongoClient(client_name)
        self.db = self.mongo_client[dbname]
    def __getitem__(self, key):
        return self.db[key]  # changed by Zuhra to be able to add a new collection before_it_was->["key"]

    def close(self):
        self.mongo_client.close()
