def get_elo_ranks(match_results):
   # first pass, figure out which user names are in the match results
   K = 15

   user_list = []
   for match in match_results:
       for (name, score) in match['participants']:
           if not name in user_list:
               user_list.append(name)

   ranks = {}
   for user in user_list:
       ranks[user] = 1000


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

       ranks[name_a] = ranks[name_a] + K*(Sa-Ea)
       ranks[name_b] = ranks[name_b] + K*(Sb-Eb)

   return ranks

if __name__ == '__main__':
    import elotron_backend as eb
    eb.setup_test_db()
    matches = eb.get_matches()

    print matches

    print get_elo_ranks(matches)
