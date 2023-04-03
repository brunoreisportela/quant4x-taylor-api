import pandas as pd
import numpy as np
import ta
import math


def pine_ema(src, length):
    alpha = 2 / (length + 1)
    sum_ = []
    sma = ta.trend.sma_indicator(src, length)
    found = False
    for i in range(len(src)):
        if np.isnan(sma[i]):
            sum_.append(sma[i])
        elif not found:
            sum_.append(sma[i])
            found = True
        else:
            sum_.append(alpha * src[i] + (1 - alpha) * sum_[i-1])
    return pd.Series(sum_)

def pine_rma(src, length):
    alpha = 1/length
    sum_ = []
    sma = ta.trend.sma_indicator(src, length)
    found = False
    for i in range(len(src)):
        if np.isnan(sma[i]):
            sum_.append(sma[i])
        elif not found:
            sum_.append(sma[i])
            found = True
        else:
            sum_.append(alpha * src[i] + (1 - alpha) * sum_[i-1])
    return pd.Series(sum_)


def pine_atr(high, low, close, length):
    return pine_rma(TrueRange(high, low, close), length)

def pine_rsi(x, y):
    x = pd.Series(x)
    u = np.maximum(x - x.shift(1), 0) 
    d = np.maximum(x.shift(1) - x, 0) 
    rs = pine_rma(u, y) / pine_rma(d, y)
    res = 100 - 100 / (1 + rs)
    return res

def CCI(src, window):
    ma = ta.trend.sma_indicator(src, window)
    diff = src-ma
    cci_ = [0]*window
    for x in range(window, len(src)):
        avg = np.mean([abs(src[x-i] - ma[x]) for i in range(window)])
        cci_.append(diff[x]/(avg* 0.015))
    return pd.Series(cci_)

def TrueRange(high, low, close):
    hl = np.abs(high-low)
    hc = np.abs(high-close.shift())
    lc = np.abs(low-close.shift())
    ranges = pd.concat([hl, hc, lc], axis=1)
    tr = np.max(ranges, axis=1)
    return pd.Series(tr)


# ========================================================================================


def normalize(_src, min_, max_): 
    _historicMin =  10e10
    _historicMax = -10e10
    out = []
    for src in _src:
        _historicMin = np.minimum(_historicMin if np.isnan(src) else src, _historicMin)
        _historicMax = np.maximum(_historicMax if np.isnan(src) else src, _historicMax)
        out.append(min_ + (max_ - min_) * (src - _historicMin) / max(_historicMax - _historicMin, 10e-10))
    return pd.Series(out)

def rescale( src, oldMin, oldMax, newMin, newMax):
    return newMin + (newMax - newMin) * (src - oldMin) / np.maximum(oldMax - oldMin, 10e-10)

def n_rsi(src, n1, n2):
    return rescale(pine_ema(pine_rsi(src, n1), n2), 0, 100, 0, 1)

def n_cci(  src,   n1,   n2):
    return normalize(pine_ema(CCI(src, n1), n2), 0, 1)

def n_wt(  src,   n1=10,   n2=11):
    ema1 =  pine_ema(src, n1)
    ema2 =  pine_ema((src - ema1).abs(), n1)
    ci = (src - ema1) / (0.015 * ema2)
    wt1 =  pine_ema(ci, n2) 
    wt2 = ta.trend.sma_indicator(wt1, 4)
    return normalize(wt1 - wt2, 0, 1)

def n_adx( highSrc,   lowSrc,   closeSrc,   n1):
    length = n1
    th = 20
    tr = TrueRange(highSrc, lowSrc, closeSrc).fillna(highSrc[0])
    hh = highSrc - highSrc.shift(1).fillna(0) 
    ll = lowSrc.shift(1).fillna(0) - lowSrc
    directionalMovementPlus = [ max(hh[i], 0) if hh[i] > ll[i] else 0  for i in range(len(closeSrc))]
    negMovement = [ max(ll[i], 0) if ll[i] > hh[i] else 0  for i in range(len(closeSrc))]
    trSmooth = [tr[0]]
    smoothDirectionalMovementPlus = [directionalMovementPlus[0]]
    smoothnegMovement = [negMovement[0]]
    for i in range(1, len(closeSrc)):
        trSmooth.append(trSmooth[i-1] - trSmooth[i-1] / length + tr[i])
        smoothDirectionalMovementPlus.append(smoothDirectionalMovementPlus[i-1] - smoothDirectionalMovementPlus[i-1] / length + directionalMovementPlus[i])
        smoothnegMovement.append(smoothnegMovement[i-1] - smoothnegMovement[i-1] / length + negMovement[i])
    trSmooth, smoothDirectionalMovementPlus, smoothnegMovement =  pd.Series(trSmooth), pd.Series(smoothDirectionalMovementPlus), pd.Series(smoothnegMovement)
    diPositive = smoothDirectionalMovementPlus / trSmooth * 100
    diNegative = smoothnegMovement / trSmooth * 100
    dx = (diPositive - diNegative).abs() / (diPositive + diNegative) * 100 
    adx = pine_rma(dx, length)
    return rescale(adx, 0, 100, 0, 1)

def filter_volatility(high, low, close, minLength=1, maxLength=10, useVolatilityFilter=False):
    recentAtr = pine_atr(high, low, close, minLength)
    historicalAtr = pine_atr(high, low, close, maxLength)
    return recentAtr > historicalAtr if useVolatilityFilter else pd.Series([True]*len(close))

def regime_filter(open_, high, low, close, src, threshold, useRegimeFilter):
    value1 = [0.0]
    value2 = [0.0]
    klmf = [0.0]
    absCurveSlope = [0.0]
    for i in range(1, len(close)):
        value1.append( 0.2 * (src[i] - src[i-1]) + 0.8 * value1[i-1])
        value2.append(0.1 * (high[i] - low[i]) + 0.8 * value2[i-1])
        omega = abs(value1[i] / value2[i])
        alpha = (-math.pow(omega,2) + math.sqrt(math.pow(omega, 4) + 16 * math.pow(omega,2))) / 8 
        klmf.append(alpha * src[i] + (1 - alpha) * klmf[i-1])
        absCurveSlope.append(abs(klmf[i] - klmf[i-1]))
    absCurveSlope = pd.Series(absCurveSlope)
    exponentialAverageAbsCurveSlope = 1.0 * pine_ema(absCurveSlope, 200)
    normalized_slope_decline = (absCurveSlope - exponentialAverageAbsCurveSlope) / exponentialAverageAbsCurveSlope
    return (normalized_slope_decline >= threshold) if useRegimeFilter else pd.Series([True]*len(close))

def filter_adx(highSrc, lowSrc, closeSrc, src, length, adxThreshold, useAdxFilter):
    tr = TrueRange(highSrc, lowSrc, closeSrc).fillna(highSrc[0])
    hh = highSrc - highSrc.shift(1).fillna(0) 
    ll = lowSrc.shift(1).fillna(0) - lowSrc
    directionalMovementPlus = [ max(hh[i], 0) if hh[i] > ll[i] else 0  for i in range(len(closeSrc))]
    negMovement = [ max(ll[i], 0) if ll[i] > hh[i] else 0  for i in range(len(closeSrc))]
    trSmooth = [tr[0]]
    smoothDirectionalMovementPlus = [directionalMovementPlus[0]]
    smoothnegMovement = [negMovement[0]]
    for i in range(1, len(closeSrc)):
        trSmooth.append(trSmooth[i-1] - trSmooth[i-1] / length + tr[i])
        smoothDirectionalMovementPlus.append(smoothDirectionalMovementPlus[i-1] - smoothDirectionalMovementPlus[i-1] / length + directionalMovementPlus[i])
        smoothnegMovement.append(smoothnegMovement[i-1] - smoothnegMovement[i-1] / length + negMovement[i])
    trSmooth, smoothDirectionalMovementPlus, smoothnegMovement =  pd.Series(trSmooth), pd.Series(smoothDirectionalMovementPlus), pd.Series(smoothnegMovement)
    diPositive = smoothDirectionalMovementPlus / trSmooth * 100
    diNegative = smoothnegMovement / trSmooth * 100
    dx = (diPositive - diNegative).abs() / (diPositive + diNegative) * 100 
    adx = pine_rma(dx, length)
    return  (adx > adxThreshold) if useAdxFilter else pd.Series([True]*len(closeSrc))