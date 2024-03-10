import socket
from argparse import ArgumentParser
import pickle
from message import Query
import pandas as pd
from constant import *
import datetime

parser = ArgumentParser()
parser.add_argument('-m', '--test_mode', dest='test_mode', default=False, type=bool,
                    help="Enter into local test mode if True, default False")
parser.add_argument('-s', '--server', dest='addr', default='127.0.0.1:8080',
                    help="Server address to query from, default local host port 8080")
args = parser.parse_args()


class Client(object):
    def __init__(self, test_mode, addr):
        self.test_mode = test_mode
        [self.host, self.port] = addr.split(":")
        self.port = int(self.port)

    def internal_test(self, inst):
        print('Query summary:')
        print('Address: ' + self.host + ':' + self.port)
        print('Instruction: ' + inst[0])
        if inst[0] != 'report':
            print('Argument: ' + inst[1])

    def prep_query(self, msg):
        msg = msg.split(" ")
        inst = msg[0]
        arg = None

        # Check num of args

        if len(msg) == 1:
            if inst != 'report':
                return self.error_prompt("Invalid command")
        elif (len(msg) == 0) or (len(msg) > 2) :
            return self.error_prompt("Incorrect number of arguments")
        else:
            arg = msg[1]
            # Check to ensure correct query sent to the server
            if inst == 'data':
                if not self.validate_dt_string(arg):
                    return self.error_prompt("Datetime format incorrect")

        return Query(inst, arg)

    def validate_dt_string(self, dt_str):
        try:
            ts = datetime.datetime.strptime(dt_str, '%Y-%m-%d-%H:%M')
        except ValueError:
            return False
        return True

    def error_prompt(self, error_message):
        print(error_message)
        return None

    def process_response(self, response_s):
        response = pickle.loads(response_s)
        if response.result == SUCCESS:
            if response.inst == DATA:
                # index_datetime = pd.to_datetime(response.data.pop('index'), format='%Y-%m-%d-%H:%M')
                ticker_index = response.data.pop('ticker')
                print(pd.DataFrame(response.data, index=ticker_index))
            elif (response.inst == ADD) or (response.inst == DELETE):
                print(response.data)
            elif response.inst == REPORT:
                print("report refreshed")  # TODO: Should I put this into response.data and print that?
        else:
            print("Action failed: " + response.data)

    def run(self):

        if self.test_mode:
            while True:
                inst = input(">>")
                inst = inst.split(" ")
                if inst[0] == 'END':
                    print("Ending local testing")
                    break
                self.internal_test(inst)
        else:

            while True:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                msg = input(">>")
                s.connect((self.host, self.port))
                query = self.prep_query(msg)
                if not query:
                    s.close()
                    continue
                query_s = pickle.dumps(query)
                print('Sending message of size: {0}'.format(len(query_s)))
                s.sendall(query_s)
                data = s.recv(PACKET_SIZE)
                self.process_response(data)
                s.close()


if __name__ == '__main__':
    client_args = vars(args)
    c = Client(**client_args)
    c.run()
