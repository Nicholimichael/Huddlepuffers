"""Shared helpers used across the platform build scripts.

Keeping these in one place avoids subtle drift between copies (e.g.
build_platform_v2 and build_extras_v3 both used to define `clean_num`
independently).
"""
import math


def clean_num(v):
    """Coerce a value to a finite float, or None.

    Accepts None / NaN / Infinity / non-numeric strings and returns None for
    them — useful before serializing to JSON (browsers reject bare NaN /
    Infinity tokens) or comparing values.
    """
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None
