def _classify_soil(m):
    if m <= 20:
        return 0   # Low
    elif m <= 30:
        return 1   # Medium
    else:
        return 2   # High


def _classify_tilt(t):
    if t <= 15:
        return 0   # Low
    elif t <= 20:
        return 1   # Medium
    else:
        return 2   # High


def predict_risk(soil_moisture, tilt):
    soil_score = _classify_soil(soil_moisture)
    tilt_score = _classify_tilt(tilt)
 
    high_count = [soil_score, tilt_score].count(2)
 
    if high_count >= 1:
        return "High"
    elif soil_score == 1 or tilt_score == 1:
        return "Medium"
    else:
        return "Low"