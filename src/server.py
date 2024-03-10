import pandas as pd
import socket
import yaml
import os
from argparse import ArgumentParser
import pickle
from data_retriever import DataRetrieverAV, DataRetrieverFH, DataRetrieverPdAV, DataRetrieverPdFH
from message import Query, Response
from constant import *

parser = ArgumentParser()
parser.add_argument('-t', '--tickers', dest='tickers', nargs='*',
                    help="list of tickers", default=['IBM'])  # Assuming a default server set up on IBM prices
parser.add_argument('-p', '--port', dest='port', default=8080, type=int,
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

        self.av_cfg = dict()
        self.fh_cfg = dict()
        self.init_dr_cfg(tickers, self.interval)

        # self.av = DataRetrieverAV(**self.av_cfg)
        # self.fh = DataRetrieverFH(**self.fh_cfg)
        self.av = DataRetrieverPdAV()  # Testing server using pandas data retriever
        self.fh = DataRetrieverPdFH()
        # TODO: handle different stitching scenarios {live trading day / outside of trading hours}
        for ticker in self.tickers:
            self.data[ticker] = self.pull_data(ticker)

        # Calculate Signal, Position, PnL
        for ticker in self.tickers:
            self.calculate_all(ticker)

        self.save_data()

        # Initialize Network
        self.host = "127.0.0.1"
        self.port = port

    def pull_data(self, ticker):
        _df = pd.concat([self.av.process_data(self.av.retrieve(ticker), ticker),
                         self.fh.process_data(self.fh.retrieve(ticker), ticker)])
        _df.index = pd.to_datetime(_df.index, format='%Y-%m-%d %H:%M:%S')
        _df.sort_index(inplace=True)
        return _df

    def save_data(self):
        pd.concat([df for df in self.data.values()]).to_csv('report.csv')

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
        datetime = pd.to_datetime(datetime, format='%Y-%m-%d-%H:%M')
        idx = pd.Series(datetime - self.data[ticker].index).abs().idxmin()  # map query datetime to nearest available
        return self.data[ticker].iloc[[idx], :][['ticker', 'price', 'signal']]

    def add_ticker(self, ticker):

        try:
            self.tickers.append(ticker)
            self.data[ticker] = self.pull_data(ticker)
            self.calculate_all(ticker)
            return SUCCESS, "Successfully added ticker {0}".format(ticker)
        except Exception as e:  # TODO: add more specific exception handling
            return ERROR, "Unable to add ticker {0}".format(ticker)

    def delete_ticker(self, ticker):
        try:
            self.tickers.remove(ticker)
            self.data.pop(ticker)
            return SUCCESS, "Successfully deleted ticker {0}".format(ticker)
        except Exception as e:  # TODO: add more specific exception handling
            return ERROR, "Unable to delete ticker {0}".format(ticker)

    def refresh_data(self):
        # Logic:
        for ticker in self.tickers:
            self.data[ticker] = self.pull_data(ticker)
            self.calculate_all(ticker)
        self.save_data()

    def process_query(self, message):
        query = pickle.loads(message)
        if query.inst == "data":
            data = pd.concat([self.query(ticker, query.arg) for ticker in self.tickers]).to_dict('list')
            # data['index'] = query.arg
            return Response(DATA, SUCCESS, data)

        elif query.inst == "add":
            result, msg = self.add_ticker(query.arg)
            return Response(ADD, result, msg)

        elif query.inst == "delete":
            result, msg = self.delete_ticker(query.arg)
            return Response(DELETE, result, msg)
        elif query.inst == "report":
            self.refresh_data()
            return Response(REPORT, SUCCESS, None)
        else:
            return Response(UNKNOWN, ERROR, "Undefined Instruction")

    def run(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))

        print("Server listening for request now")
        while True:
            s.listen()
            conn, addr = s.accept()

            with conn:
                print("Connected to client")
                data = conn.recv(PACKET_SIZE)
                if not data:
                    conn.close()
                    continue
                response = self.process_query(data)
                response_s = pickle.dumps(response)
                if len(response_s) > PACKET_SIZE:
                    # Data Check
                    response_s = pickle.dumps(Response(response.inst, ERROR, "Response payload too large."))
                print('Sending Message size: {0}'.format(len(response_s)))
                conn.sendall(response_s)
                conn.close()
                print("Service performed, connection closed")


if __name__ == '__main__':
    server_args = vars(args)
    server = Server(**server_args)
    server.run()
