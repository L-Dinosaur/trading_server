import pandas as pd
import socket
import yaml
import os
from argparse import ArgumentParser
from data_retriever import DataRetrieverAV, DataRetrieverFH
interval_map = {'5min': 5,
                '10min': 10,
                '15min': 15,
                '30min': 30,
                '60min': 60}

NUM_HOURS_TRADING_DAY = 6.5  # 9:30 to 4:00
NUM_MIN_TRADING_DAY = NUM_HOURS_TRADING_DAY * 60

parser = ArgumentParser()
parser.add_argument('-t', '--ticker', dest='tickers', nargs='*',
                    help="list of tickers", default=['SPX'])  # Assuming a default server set up on SPX prices
parser.add_argument('-p', '--port', dest='port', default=8000, type=int,
                    help='port to bind the server to, use any value over 1023')
parser.add_argument('-x', '--interval', dest='interval', default='30min',
                    help='intervals to get price data')
parser.add_argument('-m', '--test_mode', dest='test_mode', default='False', type=bool,
                    help='Test mode to use local data instead of query API')
args = parser.parse_args()


class Server(object):

    # TODO: 1 - Initialize server instance using cmd args
    # TODO: 2 - Initialize data retrievers in server
    # TODO: 3 - Implement signal, position, and p&l
    def __init__(self, tickers, port, interval, test_mode):
        _path = os.getcwd()
        with open(os.path.join(_path, r'../cfg/server_cfg.yaml')) as f:
            self.cfg = yaml.safe_load(f)
        self.interval = interval
        if test_mode:
            data_path = os.path.join(_path, '../data')
            _df = pd.concat([pd.read_csv(os.path.join(data_path, 'av_price.csv'), index_col=0),
                             pd.read_csv(os.path.join(data_path, 'fh_price.csv'), index_col=0)])
        else:
            self.av_cfg = dict()
            self.fh_cfg = dict()
            self.setup_dr_cfg(tickers, interval)
            self.av = DataRetrieverAV(**self.av_cfg)
            self.fh = DataRetrieverFH(**self.fh_cfg)
            # TODO: handle different stitching scenarios {live trading day / outside of trading hours}
            _df = pd.concat([self.av.retrieve(), self.fh.retrieve()])
        _df.index = pd.to_datetime(_df.index, format='%Y-%m-%d %H:%M:%S')
        _df.sort_index(inplace=True)
        self.data = {ticker: _df[_df['ticker'] == ticker] for ticker in tickers}
        self.host = "127.0.0.1"
        self.port = port

    def setup_dr_cfg(self, tickers, interval):
        self.av_cfg['key'] = self.cfg['AV_KEY']
        self.av_cfg['url'] = self.cfg['AV_URL']
        self.fh_cfg['key'] = self.cfg['FH_TOKEN']
        self.fh_cfg['url'] = self.cfg['FH_URL']
        self.av_cfg['interval'] = interval
        self.av_cfg['tickers'] = tickers
        self.fh_cfg['interval'] = interval
        self.fh_cfg['tickers'] = tickers

    def calculate_signal(self):
        """ Calculate signal on price series"""
        def sig(p, avg, std):
            """ Momentum Signal """
            if p > avg + std:
                return 1
            elif p < avg - std:
                return -1
            else:
                return 0

        window = int(NUM_MIN_TRADING_DAY / interval_map[self.interval])
        for ticker, df in self.data.items():
            df['rolling_avg'] = df['price'].rolling(window).mean()
            df['rolling_std'] = df['price'].rolling(window).std()
            df['signal'] = df.apply(lambda x: sig(x.price, x.rolling_avg, x.rolling_std), axis=1)
        print('signal calculated')

    def position(self):
        """ Calculate position based on signal """
        # Assuming infinite long short
        # TODO: incorporate long/short cap
        for ticker, df in self.data.items():
            df['position'] = df['signal'].cumsum().shift().fillna(0)

    def pnl(self):
        """ Calculate pnl based on position """
        for ticker, df in self.data.items():
            df['unit_return_dollar'] = df['price'].diff()
            df['pnl'] = df['position'].shift().fillna(0) * df['unit_return_dollar']

    def query(self, ticker, datetime):
        # TODO: Add query date projection onto index logic
        """ server side query function, for testing """
        print(self.data[ticker].loc[datetime, ['price', 'signal']])

    def internal_run(self):
        """ server internal run for testing """
        while True:
            user_args = input(">>").split(" ")
            if user_args[0] == 'END':
                print('ending internal run...')
                break
            datetime = pd.to_datetime(user_args[1], format='%Y-%m-%d-%H:%M')
            ticker = user_args[0]
            self.query(ticker, datetime)

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))

        while True:
            s.listen()

            conn, addr = s.accept()

            with conn:
                print("Connected to client")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    conn.sendall(data)


if __name__ == '__main__':
    server_args = vars(args)
    server = Server(**server_args)
    server.calculate_signal()
    server.internal_run()

