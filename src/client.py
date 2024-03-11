import socket
from argparse import ArgumentParser
import pickle
from message import Query
import pandas as pd
from constant import *
import datetime

parser = ArgumentParser()
parser.add_argument('-s', '--server', dest='addr', default='127.0.0.1:8080',
                    help="Server address to query from, default local host port 8080")
args = parser.parse_args()


class Client(object):
    """ Clinet CLI"""
    def __init__(self, addr):
        [self.host, self.port] = addr.split(":")
        self.port = int(self.port)

    def prep_request(self, msg):

        """ Package up request to send to server """

        # Process CLI instruction
        msg = msg.split(" ")
        inst = msg[0]
        arg = None

        # Check num of args
        if len(msg) == 1:
            if inst != 'report':
                return self.error_prompt("Invalid command")
        elif (len(msg) == 0) or (len(msg) > 2) :
            return self.error_prompt("Incorrect number of arguments")
        else:  # Correct number of arguments
            arg = msg[1]
            # validate datetime format for "data" requests
            if inst == 'data':
                if not self.validate_dt_string(arg):
                    return self.error_prompt("Datetime format incorrect")

        return Query(inst, arg)

    def validate_dt_string(self, dt_str):
        """ helper method to validate datetime format of {dt_str}"""
        try:
            ts = datetime.datetime.strptime(dt_str, '%Y-%m-%d-%H:%M')
        except ValueError:
            return False
        return True

    def error_prompt(self, error_message):
        """ helper method to print {error message} locally and return None result"""
        print(error_message)
        return None

    def process_response(self, response_s):
        """ Process response sent back from the server """
        response = pickle.loads(response_s)

        if response.result == SUCCESS:
            if response.inst == DATA:
                ticker_index = response.data.pop('ticker')
                print(pd.DataFrame(response.data, index=ticker_index))
            elif (response.inst == ADD) or (response.inst == DELETE):
                print(response.data)
            elif response.inst == REPORT:
                print("report refreshed")  # TODO: Should I put this into response.data and print that?
        else:
            print("Action failed: " + response.data)

    def run(self):
        """ Run client CLI """

        while True:  # Infinite loop to open connection, send request, process response, and close connection
            # One connection per request to free up socket resources given blocking implementation
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            msg = input(">>")
            s.connect((self.host, self.port))
            query = self.prep_request(msg)
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
