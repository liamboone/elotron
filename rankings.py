from elotron_backend import get_config

def get_elo_ranks(match_results, history=False):
    if history:
        return [rank for rank in _elo_ranks(match_results, history)]
    else:
        for rank in _elo_ranks(match_results, history):
            pass
        return rank

def _elo_ranks(match_results, history=False):
    # first pass, figure out which user names are in the match results
    K = get_config('K', 15)
    K_new = get_config('K_new_player', 30)

    new_player_period = get_config('new_player_period', 0)

    user_list = []
    for match in match_results:
        for (name, score) in match['participants']:
            if not name in user_list:
                user_list.append(name)

    ranks = {}
    num_games = {}

    for user in user_list:
        ranks[user] = 1000
        num_games[user] = 0
    
    yield ranks

    for match in match_results:
        participants = match['participants']

        (name_a, score_a) = participants[0]
        (name_b, score_b) = participants[1]

        Qa = 10.0**(ranks[name_a]/400.0)
        Qb = 10.0**(ranks[name_b]/400.0)

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

        if history:
            ranks = dict(ranks)

        K_a = K
        K_b = K
        
        if num_games[name_a] < new_player_period:
            K_a = K_new
        if num_games[name_b] < new_player_period:
            K_b = K_new

        ranks[name_a] = ranks[name_a] + K_a*(Sa-Ea)
        ranks[name_b] = ranks[name_b] + K_b*(Sb-Eb)

        num_games[name_a] += 1
        num_games[name_b] += 1

        yield ranks

if __name__ == '__main__':
    import elotron_backend as eb
    eb.setup_test_db()
    matches = eb.get_matches()

    print matches

    print get_elo_ranks(matches)
