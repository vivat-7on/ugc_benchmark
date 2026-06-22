from contextlib import contextmanager

from pymongo import MongoClient


@contextmanager
def get_mongo_db():
    client = MongoClient("localhost", 27018)
    try:
        yield client["ugc"]
    finally:
        client.close()
