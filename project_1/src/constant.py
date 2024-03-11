NUM_HOURS_TRADING_DAY = 6.5  # 9:30 to 4:00
NUM_MIN_TRADING_DAY = NUM_HOURS_TRADING_DAY * 60
PACKET_SIZE = 4096
SUCCESS = 0
ERROR = -1
DATA = 1
ADD = 2
DELETE = 3
REPORT = 4
UNKNOWN = 5

interval_map = {'5min': 5,
                '10min': 10,
                '15min': 15,
                '30min': 30,
                '60min': 60}
