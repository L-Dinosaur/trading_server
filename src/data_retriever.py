import requests
import pandas as pd


class DataRetriever(object):

    def __init__(self, key, url, interval, tickers):
        self.params = dict()
        self.params['key'] = key
        self.params['url'] = url
        self.params['interval'] = interval
        self.tickers = tickers

    def build_url(self, ticker):
        url = self.params['url'] + '&'.join([param_key + '=' + param for param_key, param in self.params.items()
                                             if param_key != 'url']) + '&symbol=' + ticker
        return url

    def preprocess(self, r, ticker):
        print("Warning: called unimplemented parent class function.")
        return pd.DataFrame()

    def retrieve(self):
        urls = {ticker: self.build_url(ticker) for ticker in self.tickers}
        dfs = [self.preprocess(requests.get(url), ticker) for ticker, url in urls.items()]
        df = pd.concat(dfs)
        return df


class DataRetrieverAV(DataRetriever):

    def __init__(self, key, url, interval, tickers):
        super(DataRetrieverAV, self).__init__(key, url, interval, tickers)
        self.params['function'] = 'TIME_SERIES_INTRADAY'
        self.params['outputsize'] = 'full'
        self.params['extended_hours'] = 'false'
        self.params['apikey'] = self.params.pop('key')

    def preprocess(self, r, ticker):
        data = r.json()
        df = pd.DataFrame(data["Time Series ({0})".format(self.params['interval'])]).transpose()
        df.drop(["1. open", "2. high", "3. low", "5. volume"], axis=1, inplace=True)
        df.rename({"4. close": "price"}, axis=1, inplace=True)
        df["ticker"] = ticker
        df.index.names = ['datetime']
        return df


class DataRetrieverFH(DataRetriever):

    def __init__(self, key, url, interval, tickers, fill_logic='flat_fill'):
        super(DataRetrieverFH, self).__init__(key, url, interval, tickers)
        self.fill_logic = fill_logic
        self.params['token'] = self.params.pop('key')

    def preprocess(self, r, ticker):
        """ flatfill or interpolate price data"""
        data = r.json()
        # TODO: account for EST/EDT
        quote_time = pd.to_datetime(data['t'], unit='s', utc=True).tz_convert('EST').tz_localize(None)
        # assume regular trading window
        beginning = pd.to_datetime(quote_time.strftime('%Y-%m-%d') + ' 09:30', format='%Y-%m-%d %H:%M')
        df_index = pd.date_range(beginning, quote_time, freq=self.params['interval'])  # TODO: address the EOD entry
        df = pd.DataFrame(index=df_index)
        df['price'] = data['c']
        df['ticker'] = ticker
        df.index.names = ['datetime']
        return df


if __name__ == '__main__':

    # 1a. test that Data Retriever for Alpha Vantage is working
    AV_KEY = '00H6LKR56TT7K8VK'
    AV_URL = 'https://www.alphavantage.co/query?'
    av = DataRetrieverAV(key=AV_KEY, url=AV_URL, tickers=['IBM', 'AAPL', 'MSFT'], interval='30min')
    res = av.retrieve()
    res.to_csv('../data/av_price.csv')

    # 1b. test that Finn Hub works, too
    # FH_TOKEN = 'cnltsshr01qut4m3uve0cnltsshr01qut4m3uveg'
    # FH_URL = 'https://finnhub.io/api/v1/quote?'
    # fh = DataRetrieverFH(key=FH_TOKEN, url=FH_URL, tickers=['IBM', 'AAPL', 'MSFT'], interval='30min')
    # res = fh.retrieve()
    # res.to_csv('../data/fh_price.csv')

