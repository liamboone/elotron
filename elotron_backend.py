from pymongo import MongoClient
import time
import calendar
import os
from itertools import permutations
from random import randint

try:
    db_name = os.environ['DB_NAME']
except KeyError:
    db_name = 'elotron-dev'

participants_collection_name = 'participants'
matches_collection_name = 'matches'

try:
    mongo_uri = os.environ['MONGOHQ_URL']
except KeyError:
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

def get_display_name(login):
    doc = prts_coll.find_one({'login':login})
    if doc == None:
        raise Exception
    
    return doc['display_name']

def get_all_users():
    logins = []
    for doc in prts_coll.find():
        logins.append(doc['login'])

    return logins

def _clear_matches():
    matches_coll.remove({})

def _clear_participants():
    prts_coll.remove({})

def setup_test_db():
    _clear_participants()
    _clear_matches()

    add_participant('Kaylee', 'ktrain')
    add_participant('Finn', 'fbomb')
    add_participant('Lucy', 'lilmike')
    add_participant('Red', 'radar')
    add_participant('Callista', 'idiot')
    add_participant('Pyrite', 'young_peezy')

    for one, two in permutations(get_all_users(), 2):
        if randint(0,1) == 1:
            one, two = two, one
        add_match([(one, 21), (two, randint(0,19))])
        print one, 'vs', two
        time.sleep(1)

if __name__ == '__main__':
    setup_test_db()
    print 'Getting matches'
    print get_matches()

    print 'Getting users'
    print get_all_users()

    print 'Getting display names'
    for login in get_all_users():
        print get_display_name(login)

