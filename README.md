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
Command Supported on the Client Side
- data YYYY-MM-DD-HH:MM (example: data 2024-02-28-12:30)
  - returns the price and signal data available in the server data set that's closest to the datetime supplied
- add TICKER (example: add AAPL)
  - instructs the server to add data for supplied ticker
- delete TICKER(example: delete AAPL)
  - instructs the server to remove data for supplied ticker
- report
  - instruct the server to refresh data and save to report.csv on server's local side

## Dependency and Data Source
- Mac OSX Monterey 12.3.1
- python 3.7 and its standard Library (argparse, socket, yaml, pickle, etc.)
- pandas 1.3.5
- _Data Source_: Alpha Vantage Intraday Series
- _Data Source_: Finn Hub Quote

## Issues Encountered and Assumptions
- Low API limit for Alpha Vantage (25 calls per day)
  - __Resolution__: Build a "fake" data retriever with the same I/O behavior that pretends to get data from Alpha Vantage, but actually reads local data using Pandas
  - __Assumption__: Not going to query for all available history, but only trailing one month which contains (in most cases) enough data points for timeseries statistics calculation
- No API available for getting intraday data for the live trading day
  - Alpha Vantage only provides up to t-1, FinnHub only provides latest quote with no near term history
  - Re-examine APIs if have more time
  - __Resolution/Assumption__: Flat fill price data for the live trading day using Finn Hub's latest quote, and stitch to Alpha Vantage historical data to maintain data frequency consistency
- Payload too large, need to optimize
  - Instead of sending "success", use int code to success/failure
  - Instead of sending requested price/signal as dataframe, use dictionary which are much less costly
## Next Steps
- Add more user input error handling logic on both client and server sides
- Write unittests for each class
- Explore other higher level (such as HTTP) APIs for the networking logic
- Explore threading to concurrently handle clients
- Fine tune some data processing logic to handle edge cases that can arise depending on time of the day or day of the week when this is used.
