from pymongo import MongoClient
import time
import calendar
import os
from itertools import permutations
from random import randint
from datetime import datetime

class DuplicateError(Exception):
    pass

try:
    db_name = os.environ['DB_NAME']
except KeyError:
    db_name = 'elotron-dev'

participants_collection_name = 'participants'
matches_collection_name = 'matches'
config_collection_name = 'config'

try:
    mongo_uri = os.environ['MONGOHQ_URL']
except KeyError:
    mongo_uri = 'mongodb://localhost:27017'

client = MongoClient(mongo_uri)

db = client[db_name]
prts_coll = db[participants_collection_name]
matches_coll = db[matches_collection_name]
config_coll = db[config_collection_name]

def timestamp_now():
    return calendar.timegm(time.gmtime())

def timestamp_month_day(mnth, dy):
    now = datetime.utcnow()
    then = now.replace(month=mnth, day=dy)

    epoch = datetime.utcfromtimestamp(0)
    delta = then-epoch

    utc_delta = datetime.now() - now + delta
    return int(round(delta.total_seconds()))

def get_config(name, default_val=None):
    doc = config_coll.find_one({name:{'$exists':True}})
    if doc == None:
        return default_val
    else:
        return doc[name]
    
def add_config(name, val):
    if config_coll.find({name:{'$exists':True}}).count() > 0:
        raise Exception

    doc = {name:val}

    config_coll.insert(doc)

def add_participant(display_name, login):
    if prts_coll.find({"login":login}).count() > 0:
        raise Exception

    doc = {'display_name': display_name,'login': login,'joined_time': timestamp_now()}

    prts_coll.insert(doc)

def check_match_duplicate(match_results, timestamp):
    matches = get_matches()

    if len(matches) == 0:
        return False

    for match in reversed(matches):
        if timestamp-match['time'] > 5:
            break

        if abs(timestamp-match['time']) < 5:
            return True

        identical = True
        for name_score in match_results:
            if name_score not in match['participants']:
                identical = False

        if identical:
            return True

    return False

def _add_match(results, timestamp):
    names = []
    scores = []

    # See if this is a double-add match
    if check_match_duplicate(results, timestamp):
        raise DuplicateError("Match flaged as duplicate.")

    for (name, score) in results:
        if prts_coll.find({"login":name}).count() == 0:
            raise Exception("Username {0} not in database.".format(name))
        names.append(name)
        scores.append(score)

    doc = {"participants": names,
        "scores": scores,
        "time": timestamp}
    matches_coll.insert(doc)

def add_match(results):
    _add_match(results, timestamp_now())

def add_match_on_day(results, month, day):
    _add_match(results, timestamp_month_day(month, day))

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

def _clear_config():
    config_coll.remove({})

def setup_test_db():
    _clear_participants()
    _clear_matches()
    _clear_config()

    add_config('K', 30)
    add_config('new_participant_period', 5)

    add_participant('Kaylee', 'ktrain')
    add_participant('Finn', 'fbomb')
    add_participant('Lucy', 'lilmike')
    add_participant('Red', 'radar')
    add_participant('Callista', 'idiot')
    add_participant('Pyrite', 'young_peezy')

    for one, two in permutations(get_all_users(), 2):
        if randint(0,1) == 1:
            one, two = two, one

        # test duplicate detection
        two_pts = randint(0, 19)
        
        for i in range(4):
            try:
                add_match([(one, 21), (two, two_pts)])
                print 'Match ok: ' + str([(one, 21), (two, two_pts)])
            except DuplicateError:
                 print 'Caught duplicate on match: ' + str([(one, 21), (two, two_pts)])

        print one, 'vs', two
        time.sleep(1)

if __name__ == '__main__':
    setup_test_db()
    print 'Getting config'
    print 'K-value: ' + str(get_config('K'))
    print 'New player quarantine period: ' + str(get_config('new_participant_period'))
    print 'Invalid config: ' + str(get_config('blarg'))

    print 'Getting matches'
    print get_matches()

    print 'Getting users'
    print get_all_users()

    print 'Getting display names'
    for login in get_all_users():
        print get_display_name(login)
