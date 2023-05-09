import json
import logging
from tradingview_ta import TA_Handler, Interval, Exchange

class Sentiment:

    symbols = [
        {
            u'symbol' : u'GC1!',
            u'screener' : u'america',
            u'exchange' : u'COMEX',
            u'interval' : u'INTERVAL_1_WEEK'
        },
        {
            u'symbol' : u'UKOIL',
            u'screener' : u'cfd',
            u'exchange' : u'FX',
            u'interval' : u'INTERVAL_1_WEEK'
        },
        {
            u'symbol' : u'SPX',
            u'screener' : u'america',
            u'exchange' : u'SP',
            u'interval' : u'INTERVAL_1_WEEK'
        },
        {
            u'symbol' : u'GBPUSD',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC',
            u'interval' : u'INTERVAL_1_WEEK'
        },
        {
            u'symbol' : u'EURUSD',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC',
            u'interval' : u'INTERVAL_1_WEEK'
        },
        {
            u'symbol' : u'USDJPY',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC',
            u'interval' : u'INTERVAL_1_WEEK'
        },
        {
            u'symbol' : u'USDCAD',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC',
            u'interval' : u'INTERVAL_1_WEEK'
        },
    ]

    def get_status(self, index):

        recommendation = "NEUTRAL"

        try:
            int_index = int(index)
            symbol = self.symbols[int_index]

            interval_to_use = Interval.INTERVAL_15_MINUTES

            if symbol[u'interval'] == "INTERVAL_30_MINUTES":
                interval_to_use = Interval.INTERVAL_30_MINUTES

            if symbol[u'interval'] == "INTERVAL_1_HOUR":
                interval_to_use = Interval.INTERVAL_1_HOUR

            if symbol[u'interval'] == "INTERVAL_2_HOURS":
                interval_to_use = Interval.INTERVAL_2_HOURS

            if symbol[u'interval'] == "INTERVAL_1_DAY":
                interval_to_use = Interval.INTERVAL_1_DAY

            if symbol[u'interval'] == "INTERVAL_1_WEEK":
                interval_to_use = Interval.INTERVAL_1_WEEK

            instrument = TA_Handler(
                symbol  = symbol[u'symbol'],
                screener= symbol[u'screener'],
                exchange= symbol[u'exchange'],
                interval= interval_to_use,
                # proxies={'http': 'http://example.com:8080'} # Uncomment to enable proxy (replace the URL).
            )

            recommendation = instrument.get_analysis().moving_averages["RECOMMENDATION"]

        except Exception as e:
            logging.critical(e, exc_info=True)  # log exception info at CRITICAL log level
            pass

        return recommendation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
