import math
import numpy as np

def rationalQuadratic(_src, _lookback, _relativeWeight, startAtBar, bar):
    _currentWeight = 0.
    _cumulativeWeight = 0.
    _size = 1
    if bar <=  startAtBar:
        return np.nan
    for i in range(_size + startAtBar + 1):
        y = _src[bar-i]
        w = math.pow(1 + (math.pow(i, 2) / ((math.pow(_lookback, 2) * 2 * _relativeWeight))), -_relativeWeight)
        _currentWeight += y*w
        _cumulativeWeight += w
    yhat = _currentWeight / _cumulativeWeight
    return yhat

def gaussian(_src, _lookback, startAtBar, bar):
    _currentWeight = 0.
    _cumulativeWeight = 0.
    _size = 1
    if bar <=  startAtBar:
        return np.nan
    for i in range(_size + startAtBar + 1):
        y = _src[bar-i] 
        w = math.exp(-math.pow(i, 2) / (2 * math.pow(_lookback, 2)))
        _currentWeight += y*w
        _cumulativeWeight += w
    yhat = _currentWeight / _cumulativeWeight
    return yhat