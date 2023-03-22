import logging
from tradingview_ta import TA_Handler, Interval, Exchange

def get_page(index):
    instrument = TA_Handler(
        symbol="UKOIL",
        screener="cfd",
        exchange="FX",
        interval=Interval.INTERVAL_15_MINUTES,
        # proxies={'http': 'http://example.com:8080'} # Uncomment to enable proxy (replace the URL).
    )

    recommendation = instrument.get_analysis().summary["RECOMMENDATION"]

    print(recommendation)

# GOLD 0 
# symbol="GC1!",
# screener="america",
# exchange="COMEX",

# BRENT OIL 1
# symbol="UKOIL",
# screener="cfd",
# exchange="FX",

# SP500 2
# symbol="SPX",
# screener="america",
# exchange="SP",

# GBPUSD 3
# symbol="GBPUSD",
# screener="forex",
# exchange="FX_IDC",

# EURUSD 4
# symbol="EURUSD",
# screener="forex",
# exchange="FX_IDC",

# USDJPY 5
# symbol="USDJPY",
# screener="forex",
# exchange="FX_IDC",

# USDCAD 6
# symbol="USDCAD",
# screener="forex",
# exchange="FX_IDC",

if __name__ == "__main__":
    try:
        get_page()
    except Exception as e:
        logging.critical(e, exc_info=True)  # log exception info at CRITICAL log level
        pass
