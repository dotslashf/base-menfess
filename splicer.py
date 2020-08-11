class Splicer(object):
    def __init__(self, tweet):
        self.tweet = tweet
        self.max_tweet_char = 280
        self.max_safe_char = 268

    def split_tweets(self):
        n_tweet = 1
        if len(self.tweet) > self.max_tweet_char:
            n_tweet = int(round((len(self.tweet) / self.max_tweet_char)+1))
        print(f'number of tweets {n_tweet}')

        tweets = []
        if n_tweet > 1:
            last_cut = 0
            is_last = False
            for i in range(0, n_tweet):
                if last_cut == 0:
                    cut = (len(self.tweet) / n_tweet) * i
                else:
                    cut = last_cut

                if i < n_tweet - 1:
                    next_cut = (len(self.tweet) / n_tweet) * (i + 1)
                    while next_cut < self.max_safe_char * (i + 1):
                        next_cut += 1
                else:
                    next_cut = len(self.tweet)
                    while next_cut < len(self.tweet):
                        next_cut += 1
                    is_last = True

                next_cut = round(next_cut)
                cut = round(cut)

                if next_cut == len(self.tweet) or self.tweet[next_cut] == ' ':
                    print('last cut')
                else:
                    print('cut')
                    try:
                        while self.tweet[next_cut] != ' ':
                            next_cut -= 1
                    except:
                        next_cut = round(len(self.tweet) / 2)

                if not is_last:
                    next_cut -= 1
                    try:
                        while self.tweet[next_cut] != ' ':
                            next_cut += 1
                    except:
                        next_cut = round(len(self.tweet)/2)

                # tweet awal
                if i == 0:
                    tweets.append(
                        self.tweet[cut:next_cut].strip() + ' ⬇️')
                # tweet antara awal dan akhir
                elif i < n_tweet - 1:
                    tweets.append(
                        '⬆️ ' + self.tweet[cut:next_cut].strip() + ' ⬇️')
                # tweet akhir
                else:
                    tweets.append('⬆️ ' + self.tweet[cut:next_cut].strip())

                print(
                    f'tweet ke: {i+1}\n------------\n{tweets[i]}')

                last_cut = next_cut
        else:
            tweets.append(self.tweet)

        return tweets