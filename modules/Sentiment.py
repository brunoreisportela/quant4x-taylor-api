import json
import logging
from tradingview_ta import TA_Handler, Interval, Exchange


class Sentiment:

    symbols = [
        {
            u'symbol' : u'GC1!',
            u'screener' : u'america',
            u'exchange' : u'COMEX'
        },
        {
            u'symbol' : u'UKOIL',
            u'screener' : u'cfd',
            u'exchange' : u'FX'
        },
        {
            u'symbol' : u'SPX',
            u'screener' : u'america',
            u'exchange' : u'SP'
        },
        {
            u'symbol' : u'GBPUSD',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC'
        },
        {
            u'symbol' : u'EURUSD',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC'
        },
        {
            u'symbol' : u'USDJPY',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC'
        },
        {
            u'symbol' : u'USDCAD',
            u'screener' : u'forex',
            u'exchange' : u'FX_IDC'
        },
    ]

    def get_status(self, index):

        recommendation = "NEUTRAL"

        try:
            int_index = int(index)
            symbol = self.symbols[int_index]

            instrument = TA_Handler(
                symbol  = symbol[u'symbol'],
                screener= symbol[u'screener'],
                exchange= symbol[u'exchange'],
                interval= Interval.INTERVAL_15_MINUTES,
                # proxies={'http': 'http://example.com:8080'} # Uncomment to enable proxy (replace the URL).
            )

            recommendation = instrument.get_analysis().summary["RECOMMENDATION"]

        except Exception as e:
            logging.critical(e, exc_info=True)  # log exception info at CRITICAL log level
            pass

        return recommendation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
