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

    doc = {'display_name': display_name,
           'login': login,
           'joined_time': timestamp_now()}

    prts_coll.insert(doc)

def get_active_players():
    '''Determine which players are active based on two conditions:
    A player is active if they have played more than [leaderboard_activity_games] 
    games in the last [leaderboard_activity_days],
    or if they have played more than [new_player_period] games overall'''

    new_player_period = get_config('new_player_period', 0)
    leaderboard_activity_days = get_config('leaderboard_activity_days', 30)
    leaderboard_activity_games = get_config('leaderboard_activity_games', 5)
   
    cur_time = timestamp_now()
    time_diff = 3600*24*leaderboard_activity_days

    recent_match_epoch = cur_time - time_diff
    state = {}
    
    for p in get_all_users():
        state[p] = {}
        state[p]['all_matches'] = 0
        state[p]['recent_matches'] = 0

    for match in get_matches():
        for p in match['participants']:
            p = p[0]
            state[p]['all_matches'] += 1
            if match['time'] >= recent_match_epoch:
                state[p]['recent_matches'] += 1

    active_state = {}
    for p in state.keys():
        active_state[p] = False
        if state[p]['all_matches'] >= new_player_period:
            active_state[p] = True
        if state[p]['recent_matches'] >= leaderboard_activity_games:
            active_state[p] = True

    return active_state

def check_match_duplicate(match_results, timestamp):
    matches = get_matches()

    if len(matches) == 0:
        return False

    # Iterate through matches, most to least recent
    for match in reversed(matches):
        if timestamp-match['time'] > 5: # if a match is more than
            break                       # 5 seconds in the past, we're good

        if timestamp-match['time'] < -5: # This check to see if we're more
            continue                     # than 5 seconds in the
                                         # _future_ is needed because
                                         # when clocks and the internet
                                         # mix, weird shit can happen

        # At this point we know that the new match is within 5 seconds

        # With ZDR on we don't even care if the match is actually a dup
        if get_config("zealous_duplicate_rejection", False):
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
