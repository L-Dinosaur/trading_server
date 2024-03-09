import socket
from argparse import ArgumentParser
import pickle


parser = ArgumentParser()
parser.add_argument('-m', '--test_mode', dest='test_mode', default=False, type=bool,
                    help="Enter into local test mode if True, default False")
parser.add_argument('-s', '--server', dest='addr', default='127.0.0.1:8000',
                    help="Server address to query from, default local host port 8000")
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
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            while True:
                msg = input(">>")
                s.sendall(bytes(msg, 'utf-8'))
                data = s.recv(1024)
                print(f"data received: {data}")


if __name__ == '__main__':
    client_args = vars(args)
    c = Client(**client_args)
    c.run()
