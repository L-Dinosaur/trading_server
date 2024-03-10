import socket
from argparse import ArgumentParser
import pickle
from message import Query, Response


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
        if len(msg) == 2:
            arg = msg[1]
        return Query(inst, arg)

    def process_response(self, response_s):
        response = pickle.loads(response_s)
        if response.result == "success":
            if response.inst == "data":
                print(response.data)
            elif response.inst == "add":
                print("Ticker: " + response.data + " added.")
            elif response.inst == "delete":
                print("Ticker: " + response.data + " deleted.")
            elif response.inst == "report":
                print("report refreshed")  # TODO: Should I put this into response.data and print that?
            else:
                print("response type not known: " + response.inst)
        else:
            print("query failed, error message: " + response.data)

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
                query_s = pickle.dumps(query)
                print('Sending message of size: {0}'.format(len(query_s)))
                s.sendall(query_s)
                data = s.recv(4096)
                self.process_response(data)
                s.close()


if __name__ == '__main__':
    client_args = vars(args)
    c = Client(**client_args)
    c.run()
