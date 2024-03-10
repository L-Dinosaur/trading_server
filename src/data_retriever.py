import requests
import pandas as pd
import os
DATA_PATH = '../data'


class DataRetriever(object):

    def __init__(self, key, url, interval):
        self.params = dict()
        self.params['key'] = key
        self.params['base_url'] = url
        self.params['interval'] = interval

    def build_url(self, ticker):
        url = self.params['base_url'] + '&'.join([param_key + '=' + param for param_key, param in self.params.items()
                                                  if param_key != 'url']) + '&symbol=' + ticker
        return url

    def retrieve(self, ticker):
        """ Retrieve raw data using ticker information and api details stored in the class"""
        r = requests.get(self.build_url(ticker))
        return r.json()

    def process_data(self, data, ticker):
        """ Process raw data using API specific formatting logic, implemented in sub-classes """
        pass


class DataRetrieverAV(DataRetriever):

    def __init__(self, key, url, interval):
        super(DataRetrieverAV, self).__init__(key, url, interval)
        self.params['function'] = 'TIME_SERIES_INTRADAY'
        self.params['outputsize'] = 'full'
        self.params['extended_hours'] = 'false'
        self.params['apikey'] = self.params.pop('key')

    def process_data(self, data, ticker):
        df = pd.DataFrame(data["Time Series ({0})".format(self.params['interval'])]).transpose()
        df.drop(["1. open", "2. high", "3. low", "5. volume"], axis=1, inplace=True)
        df.rename({"4. close": "price"}, axis=1, inplace=True)
        df["ticker"] = ticker
        df.index.names = ['datetime']
        return df


class DataRetrieverFH(DataRetriever):

    def __init__(self, key, url, interval, fill_logic='flat_fill'):
        super(DataRetrieverFH, self).__init__(key, url, interval)
        self.fill_logic = fill_logic
        self.params['token'] = self.params.pop('key')

    def process_data(self, data, ticker):
        """ flatfill data"""
        # TODO: might need to account for EST/EDT
        quote_time = pd.to_datetime(data['t'], unit='s', utc=True).tz_convert('EST').tz_localize(None)
        # assume regular trading window
        beginning = pd.to_datetime(quote_time.strftime('%Y-%m-%d') + ' 09:30', format='%Y-%m-%d %H:%M')
        df_index = pd.date_range(beginning, quote_time, freq=self.params['interval'])  # TODO: address the EOD entry
        df = pd.DataFrame(index=df_index)
        # TODO: implement more sophisticated data fill methodology such as interpolation
        df['price'] = data['c']
        df['ticker'] = ticker
        df.index.names = ['datetime']
        return df


class DataRetrieverPdAV(object):
    """ Pandas Data Retriever used for testing server logic, used to preserve api request"""
    def __init__(self):
        self.data_path = DATA_PATH

    def retrieve(self, ticker):
        return pd.read_csv(os.path.join(self.data_path, 'av_price_' + ticker + '.csv'), index_col=0)

    def process_data(self, df, ticker):
        print("passing through df for {0}".format(ticker))
        return df


class DataRetrieverPdFH(object):
    """ Pandas Data Retriever used for testing server logic, used to preserve api requests"""
    def __init__(self):
        self.data_path = DATA_PATH

    def retrieve(self, ticker):
        return pd.read_csv(os.path.join(self.data_path, 'fh_price_' + ticker + '.csv'), index_col=0)

    def process_data(self, df, ticker):
        print("passing through df for {0}".format(ticker))
        return df


if __name__ == '__main__':

    # 1a. test that Data Retriever for Alpha Vantage is working
    # AV_KEY = '00H6LKR56TT7K8VK'
    # AV_URL = 'https://www.alphavantage.co/query?'
    # av = DataRetrieverAV(key=AV_KEY, url=AV_URL, interval='30min')
    # res = av.process_data(av.retrieve('IBM'), 'IBM')
    # res.to_csv('../data/av_price.csv')

    # 1b. test that Finn Hub works, too
    FH_TOKEN = 'cnltsshr01qut4m3uve0cnltsshr01qut4m3uveg'
    FH_URL = 'https://finnhub.io/api/v1/quote?'
    fh = DataRetrieverFH(key=FH_TOKEN, url=FH_URL, interval='30min')
    res = fh.process_data(fh.retrieve('IBM'), 'IBM')
    res.to_csv('../data/fh_price.csv')

