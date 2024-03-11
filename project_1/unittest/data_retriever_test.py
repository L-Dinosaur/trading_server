import unittest
from project_1.src.data_retriever import DataRetrieverAV, DataRetrieverFH
AV_KEY = 'AC0GWZFNLV7MF4Z0'
AV_URL = 'https://www.alphavantage.co/query?'
FH_URL = 'https://finnhub.io/api/v1/quote?'
FH_TOKEN = 'cnltsshr01qut4m3uve0cnltsshr01qut4m3uveg'
SAVE_PATH = '../test_output'


class DataRetrieverTest(unittest.TestCase):
    """ DataRetriever Unit Tests"""
    def setUp(self):
        self.av = DataRetrieverAV(AV_KEY, AV_URL, '30min')
        self.fh = DataRetrieverFH(FH_TOKEN, FH_URL, '30min')

    def testAVURL(self):
        """ Test URL Building """
        url = self.av.build_url('IBM')
        self.assertIn(AV_URL, url, 'Base URL Not found in Result')
        self.assertIn('apikey=' + AV_KEY, url, 'api key Not found in Result')
        self.assertIn('symbol=IBM', url, 'symbol Not found in Result')
        self.assertIn('interval=30min', url, 'interval Not found in Result')
        self.assertIn('outputsize=full', url, 'Base URL Not found in Result')
        self.assertIn('function=TIME_SERIES_INTRADAY', url, 'api key Not found in Result')
        self.assertIn('extended_hours=false', url, 'symbol Not found in Result')

    def testFHURL(self):
        """ Test FH URL Building"""
        url = self.fh.build_url('IBM')
        self.assertIn(FH_URL, url, 'Base URL Not found in Result')
        self.assertIn('token=' + FH_TOKEN, url, 'api key Not found in Result')
        self.assertIn('symbol=IBM', url, 'symbol Not found in Result')
        self.assertIn('interval=30min', url, 'interval Not found in Result')

    def testAVData(self):
        """ Test AV Data Processing """
        self.av_raw_data = self.av.retrieve('IBM')
        self.assertIn("Time Series (30min)", self.av_raw_data.keys())
        self.assertIsNotNone(self.av_raw_data['Time Series (30min)'])

        self.av_data = self.av.process_data(self.av_raw_data, 'IBM')
        self.assertFalse(self.av_data.empty)
        self.assertIn('datetime', self.av_data.index.names)
        self.assertIn('price', self.av_data.columns)
        self.assertIn('ticker', self.av_data.columns)
        self.assertIsInstance(self.av_data['price'][0], float)

    def testFHData(self):
        """ Test FH Data Processing """
        self.fh_raw_data = self.fh.retrieve('IBM')
        self.assertIn("c", self.fh_raw_data.keys())
        self.assertIsNotNone(self.fh_raw_data['c'])
        self.assertIsInstance(self.fh_raw_data['c'], float)
        self.assertIsInstance(self.fh_raw_data['t'], int)

        self.fh_data = self.fh.process_data(self.fh_raw_data, 'IBM')
        self.assertFalse(self.fh_data.empty)
        self.assertIn('datetime', self.fh_data.index.names)
        self.assertIn('price', self.fh_data.columns)
        self.assertIn('ticker', self.fh_data.columns)

    def tearDown(self):
        """ Save test data for diagnostics """


if __name__ == '__main__':
    t = DataRetrieverTest()
    t.testFHURL()
    t.testAVURL()
    t.testAVData()
    t.testFHData()
    t.tearDown()
