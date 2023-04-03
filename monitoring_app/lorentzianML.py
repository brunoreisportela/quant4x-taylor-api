import pandas as pd
import numpy as np
import ccxt
import ta
import math
import re
import ml
import kernels

from datetime import datetime

import yfinance as yf

def get_data(symbol="BTCUSDT", timeframe="1d", ex=None, limit=500):
    data = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame.from_records(data, columns=['date', "open", "high", "low", "close", "volume"])
    df.date = df.date.apply(lambda x: datetime.utcfromtimestamp(x//1000))
    return df

def get_crypto_data(symbol="BTCUSDT", timeframe="1d", start=None, limit=500):
    print(f"Fetching {symbol} {timeframe} data{'.'*30}")
    ex = getattr(ccxt, 'binance')(); _ = ex.load_markets()
    if start is None:
        return get_data(symbol, timeframe, ex, limit)
        
    data = []
    while True:
        d = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=start, limit=1000)
        data.extend(d)
        if start == data[-1][0]:
            break
        start = data[-1][0]
    df = pd.DataFrame.from_records(data, columns=['date', "open", "high", "low", "close", "volume"])
    df.drop_duplicates(subset=['date'], keep='first', inplace=True)
    df.sort_values(by=['date'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.date = df.date.apply(lambda x: datetime.utcfromtimestamp(x//1000))
    fmt = '%Y-%m-%d %H:%m'
    print(f"{len(df)} {timeframe} candles successfully fetched for {symbol} from {df.date[0]} to {df.date[len(df)-1]}")
    return df



class Settings:
    
    def __init__(self, source, neighborsCount, maxBarsBack, featureCount, colorCompression, showExits, useDynamicExits ):
        self.source = source
        self.neighborsCount = neighborsCount
        self.maxBarsBack = maxBarsBack
        self.featureCount = featureCount
        self.colorCompression = colorCompression
        self.showExits = showExits
        self.useDynamicExits = useDynamicExits

        
class FeatureArrays:
    
    def __init__(self, f1, f2, f3, f4, f5):
        self.f1 = f1
        self.f2 = f2
        self.f3 = f3
        self.f4 = f4
        self.f5 = f5
        
        
class FeatureSeries:
    
    def __init__(self, f1, f2, f3, f4, f5):
        self.f1 = f1
        self.f2 = f2
        self.f3 = f3
        self.f4 = f4
        self.f5 = f5

        
class Label:
    
    def __init__(self, long=1, short=-1, neutral=0):
        self.long    = long
        self.short   = short
        self.neutral = neutral
    

class FilterSettings:
    
    def __init__(self, useVolatilityFilter, useRegimeFilter, useAdxFilter, regimeThreshold, adxThreshold):
        self.useVolatilityFilter = useVolatilityFilter
        self.useRegimeFilter = useRegimeFilter
        self.useAdxFilter = useAdxFilter
        self.regimeThreshold = regimeThreshold
        self.adxThreshold = adxThreshold

class Filter:
    
    def __init__(self, volatility, regime, adx):
        self.volatility = volatility
        self.regime = regime
        self.adx = adx
        

def series_from(feature_string, _close, _high, _low, _hlc3, f_paramA, f_paramB):
    return (
        ml.n_rsi(_close, f_paramA, f_paramB)   if feature_string == "RSI" else 
        ml.n_wt(_hlc3, f_paramA, f_paramB)      if feature_string == "WT"  else 
        ml.n_cci(_close, f_paramA, f_paramB)    if feature_string == "CCI" else 
        ml.n_adx(_high, _low, _close, f_paramA) if feature_string == "ADX" else None)


def get_lorentzian_distance(i, featureCount, featureSeries, featureArrays, bar):
    return (
            (math.log(1 + abs(featureSeries.f1[bar] -  featureArrays.f1[i])) + 
             math.log(1 + abs(featureSeries.f2[bar] -  featureArrays.f2[i])) + 
             math.log(1 + abs(featureSeries.f3[bar] -  featureArrays.f3[i])) + 
             math.log(1 + abs(featureSeries.f4[bar] -  featureArrays.f4[i])) + 
             math.log(1 + abs(featureSeries.f5[bar] -  featureArrays.f5[i])))
            if featureCount == 5 else
            (math.log(1 + abs(featureSeries.f1[bar] -  featureArrays.f1[i])) +
             math.log(1 + abs(featureSeries.f2[bar] -  featureArrays.f2[i])) +
             math.log(1 + abs(featureSeries.f3[bar] -  featureArrays.f3[i])) +
             math.log(1 + abs(featureSeries.f4[bar] -  featureArrays.f4[i])))
            if featureCount == 4 else
            (math.log(1 + abs(featureSeries.f1[bar] -  featureArrays.f1[i])) +
             math.log(1 + abs(featureSeries.f2[bar] -  featureArrays.f2[i])) +
             math.log(1 + abs(featureSeries.f3[bar] -  featureArrays.f3[i])))
            if featureCount == 3 else
            (math.log(1 + abs(featureSeries.f1[bar] -  featureArrays.f1[i])) +
             math.log(1 + abs(featureSeries.f2[bar] -  featureArrays.f2[i])))
            if featureCount == 2 else None
            )
        

def indicator(df):
    open_, high, low, close = df.open, df.high, df.low, df.close

    # Settings Object: General User-Defined Inputs
    settings = Settings(source=close, 
                        neighborsCount=8, 
                        maxBarsBack=2000, 
                        featureCount=2 ,
                        colorCompression=1 ,
                        showExits=False, 
                        useDynamicExits=False)

    # Trade Stats Settings
    # Note: The trade stats section is NOT intended to be used as a replacement for proper backtesting. It is intended to be used for calibration purposes only.
    # showTradeStats = rangingmarketconditions 
    useWorstCase = False 
    ohlc4 = (open_+high+low+close)/4
    hlc3 = (high+low+close)/3
    # Settings object for user-defined settings
    filterSettings = FilterSettings(useVolatilityFilter= True,
                                    useRegimeFilter= True,
                                    useAdxFilter = False,
                                    regimeThreshold = -0.1,
                                    adxThreshold = 20) 

    # Filter object for filtering the ML predictions
    filter_ =Filter(
       ml.filter_volatility(high, low, close, 1, 10, filterSettings.useVolatilityFilter), 
       ml.regime_filter(open_, high, low, close, ohlc4, filterSettings.regimeThreshold, filterSettings.useRegimeFilter),
       ml.filter_adx(high, low, close, settings.source, 14, filterSettings.adxThreshold, filterSettings.useAdxFilter)
      )
    
    # Feature Variables: User-Defined Inputs for calculating Feature Series. 
    f1_string = "RSI" 
    f1_paramA = 14 
    f1_paramB = 1 
    f2_string = "WT" 
    f2_paramA = 10 
    f2_paramB = 11 
    f3_string = "CCI" 
    f3_paramA = 20 
    f3_paramB = 1 
    f4_string = "ADX" 
    f4_paramA = 20 
    f4_paramB = 2 
    f5_string = "RSI" 
    f5_paramA = 9 
    f5_paramB = 1 

    # FeatureSeries Object: Calculated Feature Series based on Feature Variables
    featureSeries = FeatureSeries(
       series_from(f1_string, close, high, low, hlc3, f1_paramA, f1_paramB), # f1
       series_from(f2_string, close, high, low, hlc3, f2_paramA, f2_paramB), # f2 
       series_from(f3_string, close, high, low, hlc3, f3_paramA, f3_paramB), # f3
       series_from(f4_string, close, high, low, hlc3, f4_paramA, f4_paramB), # f4
       series_from(f5_string, close, high, low, hlc3, f5_paramA, f5_paramB)  # f5
     )
    
    # FeatureArrays Object: Storage of the calculated FeatureArrays into a single object
    featureArrays =  FeatureArrays(
      featureSeries.f1, # f1
      featureSeries.f2, # f2
      featureSeries.f3, # f3
      featureSeries.f4, # f4
      featureSeries.f5  # f5
     )

    # Label Object: Used for classifying historical data as training data for the ML Model:
    direction = Label(long=1, short=-1, neutral=0 )

    # EMA Settings 
    useEmaFilter = False 
    emaPeriod = 200 
    useSmaFilter = False 
    smaPeriod = 200 

    EMA = ta.trend.ema_indicator(close, emaPeriod)
    SMA = ta.trend.sma_indicator(close, smaPeriod)

    EMAUP = [close[i] > ema for i, ema in enumerate(EMA)]
    EMADN = [close[i] < ema for i, ema in enumerate(EMA)]

    SMAUP = [close[i] > sma for i, sma in enumerate(SMA)]
    SMADN = [close[i] < sma for i, sma in enumerate(SMA)]

    isEmaUptrend =  EMAUP if useEmaFilter else [True]*len(close)
    isEmaDowntrend =  EMADN if useEmaFilter else [True]*len(close)

    isSmaUptrend = SMAUP if useSmaFilter else [True]*len(close)
    isSmaDowntrend = SMADN if useSmaFilter else [True]*len(close)


    # Nadaraya-Watson Kernel Regression Settings
    useKernelFilter = True 
    showKernelEstimate = True 
    useKernelSmoothing = False 
    h = 8 
    r = 8. 
    x = 25 
    lag = 2 

    # Display Settings
    showBarColors = True 
    showBarPredictions = True 
    useAtrOffset = False 
    barPredictionsOffset = 0 

    src = settings.source
    
    last_bar_index = len(close)-1
    maxBarsBackIndex = (last_bar_index - settings.maxBarsBack) if last_bar_index >= settings.maxBarsBack else 0
    
    long = False
    short = False

    long_, short_, est = [], [], []
    yhat1, yhat2 = [], []
    y_train_array = []

    # Variables used for ML Logic
    predictions = []
    prediction = 0.
    signal = []
    distances = []

    startLongTrade = False
    startShortTrade = False

    for i in range(len(close)):
        # Derived from General Settings

        last_bar_index = i-1
        bar_index = i
        y_train_array.append((direction.short if src[i-4] < src[i-0] else direction.long if src[i-4] > src[i-0] else direction.neutral) if i >=4 else 0)

        size = min(settings.maxBarsBack-1, len(y_train_array)-1)
        sizeLoop = min(settings.maxBarsBack-1, size)
        lastDistance = -1
        prediction = None
        if bar_index >= maxBarsBackIndex:
            for j in range(sizeLoop+1): 
                d = get_lorentzian_distance(j, settings.featureCount, featureSeries, featureArrays, bar_index) 
                if d >= lastDistance and j%4: 
                    lastDistance = d          
                    distances.append(d)
                    predictions.append(round(y_train_array[j]))
                    if len(predictions) > settings.neighborsCount: 
                        lastDistance = distances[round(settings.neighborsCount*3/4)]
                        distances.pop(0)
                        predictions.pop(0)
            prediction = sum(predictions)

        # User Defined Filters: Used for adjusting the frequency of the ML Model's predictions
        filter_all = filter_.volatility[i] and filter_.regime[i] and filter_.adx[i]
        if prediction is None:
            signal.append(direction.neutral)
        else:
            signal.append(direction.long if prediction > 0 and filter_all else direction.short if prediction < 0 and filter_all else direction.neutral)

        # Fractal Filters: Derived from relative appearances of signals in a given time series fractal/segment with a default length of 4 bars
        isDifferentSignalType = signal[i] - signal[i-1] if len(signal) >= 1 else 0
        isEarlySignalFlip = signal[i] - signal[i-1] and (signal[i-1]-signal[i-2]) or (signal[i-2]-signal[i-3]) or (signal[i-3]-signal[i-4]) if len(signal) >= 4 else False
        isBuySignal = signal[i] == direction.long and isEmaUptrend[i] and isSmaUptrend[i]
        isSellSignal = signal[i] == direction.short and isEmaDowntrend[i] and isSmaDowntrend[i]
        isLastSignalBuy = signal[i-4] == direction.long and isEmaUptrend[i-4] and isSmaUptrend[i-4] if len(signal) >= 4 else False
        isLastSignalSell = signal[i-4] == direction.short and isEmaDowntrend[i-4] and isSmaDowntrend[i-4] if len(signal) >= 4 else False
        isNewBuySignal = isBuySignal and isDifferentSignalType
        isNewSellSignal = isSellSignal and isDifferentSignalType

        if i > x:
            yhat1.append(kernels.rationalQuadratic(settings.source, h, r, x, i))
            yhat2.append(kernels.gaussian(settings.source, h-lag, x, i))
        else:
            yhat1.append(0)
            yhat2.append(0)
            continue

        kernelEstimate = yhat1[i]
        # Kernel Rates of Change
        wasBearishRate = yhat1[i-2] > yhat1[i-1]
        wasBullishRate = yhat1[i-2] < yhat1[i-1]
        isBearishRate = yhat1[i-1] > yhat1[i]
        isBullishRate = yhat1[i-1] < yhat1[i]
        isBearishChange = isBearishRate and wasBullishRate
        isBullishChange = isBullishRate and wasBearishRate

        isBullishSmooth = yhat2[i] >= yhat1[i]
        isBearishSmooth = yhat2[i] <= yhat1[i]

        isBullish = (isBullishSmooth if useKernelSmoothing else isBullishRate) if useKernelFilter else True
        isBearish = (isBearishSmooth if useKernelSmoothing else isBearishRate) if useKernelFilter else True

        # Entry Conditions: Booleans for ML Model Position Entries
        startLongTrade = isNewBuySignal and isBullish and isEmaUptrend[i] and isSmaUptrend[i]
        startShortTrade = isNewSellSignal and isBearish and isEmaDowntrend[i] and isSmaDowntrend[i]
        
        if startLongTrade or startShortTrade:
            long = bool(startLongTrade)
            short = bool(startShortTrade)

            print(f"{df.date[i]}\t\tLong:\t{startLongTrade}\t\tShort:\t{startShortTrade}")

        
        long_.append(bool(startLongTrade))
        short_.append(bool(startShortTrade))
        est.append(kernelEstimate)
    
    if long:
        print("THE LATEST RESULT IS LONG")
    if short:
        print("THE LATEST RESULT IS SHORT")

    return pd.DataFrame({'date': df.date[(len(df.date)-len(long_)):],
                         'long': long_,
                         'short': short_,
                         'KrenelEstimate': est})

def get_quote_from_asset():
    # Set the ticker as 'EURUSD=X'
    # forex_data = yf.download('EURUSD=X', start='2019-01-02', end='2021-12-31')
    # Set the index to a datetime object
    # forex_data.index = pd.to_datetime(forex_data.index)
    # Display the last five rows
    # forex_data.tail()

    # Set the ticker as 'EURUSD=X'
    forex_data_minute = yf.download('USDJPY=X', period='60d', interval='15m')
    # Set the index to a datetime object
    forex_data_minute.index = pd.to_datetime(forex_data_minute.index)
    # Display the last five rows
    forex_data_minute.tail()

    forex_data_array = []

    for index in range(len(forex_data_minute.Open.values)):
        object_to_import = { "date": forex_data_minute.index.values[index], "open": forex_data_minute.Open.values[index], "high": forex_data_minute.High.values[index], "low": forex_data_minute.Low.values[index], "close": forex_data_minute.Close.values[index], "volume": forex_data_minute.Volume.values[index] }
        forex_data_array.append(object_to_import)

    forex_data_minute = pd.DataFrame(forex_data_array)

    return forex_data_minute

if __name__ == "__main__":
    
    df_data = get_quote_from_asset()

    # symbol = 'BTCUSDT'
    # interval = '15m'
    # df = get_crypto_data(symbol=symbol, timeframe=interval, start=int(datetime(year=2023, month=3, day=29).timestamp()*1000))
    # print(df)

    print(f"Running Indicator{'.'*30}")
    print("="*120)

    # out = indicator(df)
    out = indicator(df_data)
    # print("Saving results to results.csv")
    # out.to_csv('results.csv', index=False)