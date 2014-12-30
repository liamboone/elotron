from elotron_backend import get_config

def get_elo_ranks(match_results, history=False, players=[]):
    if history:
        return [(s, t) for s, t in _elo_ranks(match_results, history, players)]
    else:
        for s, t in _elo_ranks(match_results, history, players):
            pass
        return s, t

def _elo_ranks(match_results, history=False, players=[]):
    # first pass, figure out which user names are in the match results
    K = get_config('K', 15)
    K_new = get_config('K_new_player', 30)

    new_player_period = get_config('new_player_period', 0)

    user_list = []
    for match in match_results:
        for (name, score) in match['participants']:
            if not name in user_list:
                user_list.append(name)

    if players == []:
        players = user_list

    players = [p for p in players if p in user_list]

    state = {}
    time = 0
    ranks = {}
    num_games = {}

    for user in user_list:
        state[user] = {}
        #ranks[user] = 1000
        #num_games[user] = 0
        state[user]['rank'] = 1000
        state[user]['num_matches'] = 0
        state[user]['last_match'] = None
        state[user]['rank_change'] = None

    #yield (ranks, num_games)
    #yield (dict({u:dict(state[u]) for u in players}), None)

    for match in match_results:
        participants = match['participants']
        part_names = [p[0] for p in participants]

        (name_a, score_a) = participants[0]
        (name_b, score_b) = participants[1]

        Qa = 10.0**(state[name_a]['rank']/400.0)
        Qb = 10.0**(state[name_b]['rank']/400.0)

        Ea = Qa / (Qa + Qb)
        Eb = Qb / (Qa + Qb)

        if score_a > score_b:
            Sa = 1.0
            Sb = 0.0
        elif score_a < score_b:
            Sa = 0.0
            Sb = 1.0
        else:
            Sa = 0.5
            Sb = 0.5

        #if history:
        #    ranks = dict(ranks)

        K_a = K
        K_b = K

        if state[name_a]['num_matches'] < new_player_period:
            K_a = K_new
        if state[name_b]['num_matches'] < new_player_period:
            K_b = K_new
        rank_change_a = K_a*(Sa-Ea)
        rank_change_b = K_b*(Sb-Eb)

        state[name_a]['rank_change']=rank_change_a
        state[name_b]['rank_change']=rank_change_b
        state[name_a]['last_match']=match
        state[name_b]['last_match']=match
        state[name_a]['rank'] = state[name_a]['rank'] + rank_change_a
        state[name_b]['rank'] = state[name_b]['rank'] + rank_change_b

        state[name_a]['num_matches'] += 1
        state[name_b]['num_matches'] += 1

        #yield (ranks, num_games)
        if len([p for p in players if p in part_names]) > 0:
            yield (dict({u:dict(state[u]) for u in part_names + players}), match['time'])

if __name__ == '__main__':
    import elotron_backend as eb
    #eb.setup_test_db()
    matches = eb.get_matches()

    #print matches
    print get_elo_ranks(matches, history=False, players=['lilmike', 'young_peezy'])
    #print get_elo_ranks(matches)
