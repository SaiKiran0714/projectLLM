from pint import UnitRegistry

ureg = UnitRegistry()

OPS = {
    ">":  lambda a, b: a > b,
    "≥":  lambda a, b: a >= b,
    ">=": lambda a, b: a >= b,
    "=":  lambda a, b: abs(a - b) < 1e-9,
    "≤":  lambda a, b: a <= b,
    "<=": lambda a, b: a <= b,
    "<":  lambda a, b: a < b,
}

def normalize(value: float, from_unit: str, to_unit: str) -> float:
    """Convert value from from_unit to to_unit using Pint."""
    return (value * ureg.parse_units(from_unit)).to(to_unit).magnitude

def validate_row(req: dict, test: dict) -> dict:
    """
    req:  {"comparator": str, "value": float, "unit": str}
    test: {"measured_value": float, "unit": str}
    """
    try:
        mv = normalize(test["measured_value"], test["unit"], req["unit"])
    except Exception:
        return {"status": "unknown", "reason": "unit_conversion_failed"}

    op = OPS.get(req["comparator"])
    if not op:
        return {"status": "unknown", "reason": "invalid_comparator"}

    ok = op(mv, req["value"])
    return {
        "status": "pass" if ok else "fail",
        "measured_norm": mv,
        "target": req["value"],
        "unit": req["unit"],
    }
