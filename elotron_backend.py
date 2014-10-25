from pymongo import MongoClient
import time
import calendar

db_name = 'elotron-dev'
participants_collection_name = 'participants'
matches_collection_name = 'matches'

mongo_uri = 'mongodb://localhost:27017'

client = MongoClient(mongo_uri)

db = client[db_name]
prts_coll = db[participants_collection_name]
matches_coll = db[matches_collection_name]

def timestamp_now():
    return calendar.timegm(time.gmtime())

def add_participant(display_name, login):
    if prts_coll.find({"login":login}).count() > 0:
        raise Exception

    doc = {'display_name': display_name,'login': login,'joined_time': timestamp_now()}
    
    prts_coll.insert(doc)

def add_match(results):
    names = []
    scores = []
    for (name, score) in results:
        if prts_coll.find({"login":name}).count() == 0:
            raise Exception
        names.append(name)
        scores.append(score)

    doc = {"participants": names,
        "scores": scores,
        "time": timestamp_now()}
    matches_coll.insert(doc)

def get_participant_name(login):
    doc = prts_coll.find_one({"login":login})

    if doc==None:
        return None

    return doc['display_name']

def get_matches():
    docs = matches_coll.find().sort("time")

    matches = []

    for doc in docs:
        match = {}
        match['participants'] = zip(doc['participants'], doc['scores'])
        match['time'] = doc['time']
        matches.append(match)

    return matches

def __clear_matches():
    matches_coll.remove({})
if __name__ == '__main__':
    try:
        add_participant('Fred', 'fdawg') 
    except:
        pass
    try:
        add_participant('James', 'jtrain')
    except:
        pass
    __clear_matches()

    match_result = [('fdawg', 17), ('jtrain', 12)]
    add_match(match_result)
    add_match([('fdawg', 6), ('jbomb',21)])
    for x in matches_coll.find():
        print(x)
    print 'Getting matches'
    print get_matches()
