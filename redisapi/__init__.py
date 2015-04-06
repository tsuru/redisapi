import os


def mongodb_database():
    mongodb_uri = os.environ.get(
        "MONGODB_URI", os.environ.get("DBAAS_MONGODB_ENDPOINT", "mongodb://localhost:27017/"))
    database_name = os.environ.get("DATABASE_NAME", "redisapi")

    from pymongo import MongoClient
    from pymongo.errors import ConfigurationError
    client = MongoClient(mongodb_uri)
    try:
        database_name = client.get_default_database()
    except ConfigurationError:
        pass
    return client[database_name]
