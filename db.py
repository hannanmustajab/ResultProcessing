from pymongo import MongoClient

url='mongodb://127.0.0.1:27017'
cluster=MongoClient(url)
db = cluster["admissions"]
collection = db["students"]
courses_collection = db["courses"]
merit = db['merit']
chance_memo_collection = db['chance_memo']

def resetAll(collection,merit,courses_collection,chance_memo_collection):
    collection.remove()
    merit.remove()
    courses_collection.remove()
    chance_memo_collection.remove()
    return True