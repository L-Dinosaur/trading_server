import pandas as pd
import socket
import yaml
import os
from argparse import ArgumentParser
import pickle
from data_retriever import DataRetrieverAV, DataRetrieverFH
from message import Query, Response

interval_map = {'5min': 5,
                '10min': 10,
                '15min': 15,
                '30min': 30,
                '60min': 60}

NUM_HOURS_TRADING_DAY = 6.5  # 9:30 to 4:00
NUM_MIN_TRADING_DAY = NUM_HOURS_TRADING_DAY * 60

parser = ArgumentParser()
parser.add_argument('-t', '--tickers', dest='tickers', nargs='*',
                    help="list of tickers", default=['SPX'])  # Assuming a default server set up on SPX prices
parser.add_argument('-p', '--port', dest='port', default=8000, type=int,
                    help='port to bind the server to, use any value over 1023')
args = parser.parse_args()


class Server(object):

    # TODO: Add Unit Test
    # TODO: Add User Input Error Handling
    def __init__(self, tickers, port):
        # Initialization of config parameters
        _path = os.getcwd()
        with open(os.path.join(_path, r'../cfg/server_cfg.yaml')) as f:
            self.cfg = yaml.safe_load(f)
        self.interval = self.cfg['interval']
        self.tickers = tickers

        # Initialize data
        self.data = dict()
        # if self.cfg['local_data_mode']:
        #     data_path = os.path.join(_path, '../data')
        #     _df = pd.concat([pd.read_csv(os.path.join(data_path, 'av_price.csv'), index_col=0),
        #                      pd.read_csv(os.path.join(data_path, 'fh_price.csv'), index_col=0)])
        #     _df.index = pd.to_datetime(_df.index, format='%Y-%m-%d %H:%M:%S')
        #     _df.sort_index(inplace=True)
        #     self.data = {ticker: _df[_df['ticker'] == ticker] for ticker in tickers}
        # else:
        #     self.av_cfg = dict()
        #     self.fh_cfg = dict()
        #     self.init_dr_cfg(tickers, self.interval)
        #     self.av = DataRetrieverAV(**self.av_cfg)
        #     self.fh = DataRetrieverFH(**self.fh_cfg)
        #     # TODO: handle different stitching scenarios {live trading day / outside of trading hours}
        #     for ticker in self.tickers:
        #         self.data[ticker] = self.pull_data(ticker)
        #
        # # Calculate Signal, Position, PnL
        # for ticker in self.tickers:
        #     self.calculate_all(ticker)

        # Initialize Network
        self.host = "127.0.0.1"
        self.port = port

    def pull_data(self, ticker):
        _df = pd.concat([self.av.process_data(self.av.retrieve(ticker), ticker),
                         self.fh.process_data(self.fh.retrieve(ticker), ticker)])
        _df.index = pd.to_datetime(_df.index, format='%Y-%m-%d %H:%M:%S')
        _df.sort_index(inplace=True)
        return _df

    def init_dr_cfg(self, tickers, interval):
        self.av_cfg['key'] = self.cfg['AV_KEY']
        self.av_cfg['url'] = self.cfg['AV_URL']
        self.fh_cfg['key'] = self.cfg['FH_TOKEN']
        self.fh_cfg['url'] = self.cfg['FH_URL']
        self.av_cfg['interval'] = interval
        self.av_cfg['tickers'] = tickers
        self.fh_cfg['interval'] = interval
        self.fh_cfg['tickers'] = tickers

    def calculate_signal(self, ticker):
        """ Calculate signal on price series"""

        def sig(p, avg, std):
            """ Momentum Signal """
            if p > avg + std:
                return 1
            elif p < avg - std:
                return -1
            else:
                return 0
        df = self.data[ticker]
        window = int(NUM_MIN_TRADING_DAY / interval_map[self.interval])
        df['rolling_avg'] = df['price'].rolling(window).mean()
        df['rolling_std'] = df['price'].rolling(window).std()
        df['signal'] = df.apply(lambda x: sig(x.price, x.rolling_avg, x.rolling_std), axis=1)
        self.data[ticker] = df

    def calculate_position(self, ticker):
        """ Calculate position based on signal """
        # Assuming infinite long short
        # TODO: incorporate long/short cap
        df = self.data[ticker]
        df['position'] = df['signal'].cumsum().shift().fillna(0)
        self.data[ticker] = df

    def calculate_pnl(self, ticker):
        """ Calculate pnl based on position """
        df = self.data[ticker]
        df['unit_return_dollar'] = df['price'].diff()
        df['pnl'] = df['position'].shift().fillna(0) * df['unit_return_dollar']
        self.data[ticker] = df

    def calculate_all(self, ticker):
        self.calculate_signal(ticker)
        self.calculate_position(ticker)
        self.calculate_pnl(ticker)

    def query(self, ticker, datetime):
        """ server side query function, for testing """
        idx = (datetime - self.data[ticker].index).idxmin()
        print(self.data[ticker].loc[idx, ['price', 'signal']])

    def data_dummy(self):
        print("data request returned")

    def add_ticker(self, ticker):

        self.tickers.append(ticker)
        self.data[ticker] = self.pull_data(ticker)
        self.calculate_all(ticker)

    def add_ticker_dummy(self, ticker):
        print("ticker {0} added".format(ticker))

    def delete_ticker(self, ticker):
        self.tickers.remove(ticker)
        self.data.pop(ticker)

    def delete_ticker_dummy(self, ticker):
        print("ticker {0} deleted".format(ticker))

    def refresh_data(self):
        # Logic:
        for ticker in self.tickers:
            self.data[ticker] = self.pull_data(ticker)
            self.calculate_all(ticker)

    def refresh_data_dummy(self):
        print("data refreshed")

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

    def process_query(self, message):
        query = pickle.loads(message)
        if query.inst == "data":
            # data = pd.concat([df.loc[query.arg, ['ticker', 'price']] for df in self.data.values()])
            # return Response("data", "success", data)
            self.data_dummy()
            return Response("data", "success", None)
        elif query.inst == "add":
            # self.add_ticker(query.arg)
            # return Response("add", "success", None)
            self.add_ticker_dummy(query.arg)
            return Response("add", "success", None)
        elif query.inst == "delete":
            # self.delete_ticker(query.arg)
            self.delete_ticker_dummy(query.arg)
            return Response("delete", "success", None)
        elif query.inst == "report":
            # self.refresh_data()
            # TODO: to csv
            self.refresh_data_dummy()
            return Response("report", "success", None)
        else:
            return Response(query.inst, "failure", "Undefined Instruction")

    def run(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))

        print("Server listening for request now")
        while True:
            s.listen()
            conn, addr = s.accept()

            with conn:
                print("Connected to client")
                data = conn.recv(4096)
                if not data:
                    break
                response = self.process_query(data)
                response_s = pickle.dumps(response)
                conn.sendall(response_s)
                conn.close()
                print("Service performed, connection closed")


if __name__ == '__main__':
    server_args = vars(args)
    server = Server(**server_args)
    server.run()

