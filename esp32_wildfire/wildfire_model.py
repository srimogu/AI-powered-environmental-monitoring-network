def _classify_temp(t):
    if t <= 40:
        return 0   # Low
    elif t <= 65:
        return 1   # Medium
    else:
        return 2   # High


def _classify_humidity(h):
    # Higher humidity = safer (Low), lower humidity = riskier (High)
    if h >= 50:
        return 0   # Low
    elif h >= 30:
        return 1   # Medium
    else:
        return 2   # High


def _classify_smoke(s):
    if s <= 20:
        return 0   # Low
    elif s <= 40:
        return 1   # Medium
    else:
        return 2   # High


def _classify_wind(w):
    if w <= 5:
        return 0   # Low
    elif w <= 10:
        return 1   # Medium
    else:
        return 2   # High


def predict_risk(temp, humidity, wind, smoke):
    scores = [
        _classify_temp(temp),
        _classify_humidity(humidity),
        _classify_smoke(smoke),
        _classify_wind(wind),
    ]

    high_count = scores.count(2)
    medium_count = scores.count(1)

    # Overall HIGH only if at least 3 of the 4 sensors are individually High
    if high_count >= 3:
        return "High"
    # Otherwise, some risk if at least 1 sensor is High or 2+ are Medium
    elif high_count >= 1 or medium_count >= 2:
        return "Medium"
    else:
        return "Low"