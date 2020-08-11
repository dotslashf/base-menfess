max_limit = 280
tweet = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi viverra ullamcorper dolor, in auctor neque posuere non. Maecenas blandit enim tortor, sit amet sagittis purus ultricesasdsadasd non. Ut turpis risus, asdasdsadadsadsadmaximus in sapien in, facilisis rhoncus dui. In euismod leo id felis facilisis fermentum. In blandit felis felis, et tristique tellus laoreet in. Suspen quam nunc. Nulla facilisi. Suspendisse ante felis, fermentum eu fermentum eu, maximuswwwwww convallis ante. Donec dictum tellus sit amet hendrerit faucibus. Donec aliquet sem est disse pasdasdsadotenti. Sed ac quam nunc. Nulla facilisi. Suspendisse ante felis, fermentum eu fermentum eu, maximuswwwwww convallis ante. Donec dictum tellus sit amet hendrerit faucibus. Donec aliquet sem est. Duis ac quam nunc. Nulla facilisi. Suspendisse ante felis, fermentum eu fermentum eu, maximuswwwwww convallis ante. Donec dictum tellus sit amet hendrerit faucibus. Donec aliquet sem est nisi dolordfddfdfdf. Nulla facilisi."


def split_tweets(tweet):
    print(len(tweet))
    n_tweet = 1
    if len(tweet) > 280:
        n_tweet = int(round((len(tweet) / 280)+1))
    print(f'number of tweets {n_tweet}')

    tweets = []
    if n_tweet > 1:
        last_cut = 0
        is_last = False
        for i in range(0, n_tweet):
            if last_cut == 0:
                cut = (len(tweet) / n_tweet) * i
            else:
                cut = last_cut

            if i < n_tweet - 1:
                next_cut = (len(tweet) / n_tweet) * (i + 1)
                while next_cut < 268 * (i + 1):
                    next_cut += 1
                print('iterasi:', i, (272 * (i + 1) - 280))
            else:
                next_cut = len(tweet)
                while next_cut < len(tweet):
                    next_cut += 1
                is_last = True

            next_cut = round(next_cut)
            cut = round(cut)

            if next_cut == len(tweet) or tweet[next_cut] == ' ':
                print('last cut')
            else:
                print('cut')
                try:
                    while tweet[next_cut] != ' ':
                        next_cut -= 1
                except:
                    next_cut = round(len(tweet) / 2)

            if not is_last:
                next_cut -= 1
                try:
                    while tweet[next_cut] != ' ':
                        next_cut += 1
                except:
                    next_cut = round(len(tweet)/2)

            last_cut = next_cut
            if i >= 0:
                if i != 0:
                    tweets.append(
                        '-c- ' + tweet[cut:next_cut].strip() + ' -c-')
                else:
                    tweets.append(tweet[cut:next_cut].strip() + ' -c-')
    else:
        tweets.append(tweet)

    return tweets


tweets = split_tweets(tweet)
for i in tweets:
    print(len(i), i)
    print('----')
