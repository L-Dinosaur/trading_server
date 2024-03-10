# trading_server
A Trading Server that backtests a simple momentum strategy against interested stocks

## To try it out:
run server
```
python server.py --tickers IBM --port 8080
```
run client
```commandline
python client.py --server 127.0.0.1:8080
```
Command Supported
- data YYYY-MM-DD-HH:MM (example: data 2024-02-28-12:30)
  - returns the price and signal data available in the server data set that's closest to the datetime supplied
- add TICKER (example: add AAPL)
  - instructs the server to add data for supplied ticker
- delete TICKER(example: delete AAPL)
  - instructs the server to remove data for supplied ticker
- report
  - instruct the server to refresh data and save to report.csv on server's local side

## Dependency Used
- Mac OSX Monterey 12.3.1
- python 3.7 and its standard Library (argparse, socket, yaml, pickle, etc.)
- pandas 1.3.5

## Next Steps
- Add more user input error handling logic on both client and server sides
- Write unittests for each class
- Explore other higher level APIs for the networking logic
- 