def _classify_so2(v):
    if v < 50:
        return 0   # Low
    elif v <= 150:
        return 1   # Medium
    else:
        return 2   # High


def _classify_nox(v):
    if v < 100:
        return 0   # Low
    elif v <= 300:
        return 1   # Medium
    else:
        return 2   # High


def _classify_co(v):
    if v < 50:
        return 0   # Low
    elif v <= 100:
        return 1   # Medium
    else:
        return 2   # High


def predict_risk(so2, nox, co):
    scores = [_classify_so2(so2), _classify_nox(nox), _classify_co(co)]

    high_count = scores.count(2)

    # Any single pollutant exceeding its legal limit -> overall High
    if high_count >= 1:
        return "High"

    if 1 in scores:
        return "Medium"

    return "Low"