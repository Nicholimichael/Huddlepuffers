"""
diagnose_nfl.py — Figure out exactly why fetch_nfl_stats.py isn't populating tables.

Prints specific version info, tests the import, tests one API call, and reports
the exact error. Run with: python3 diagnose_nfl.py
"""

import sys
import traceback

print(f"Python: {sys.version}")
print(f"Python path: {sys.executable}")
print()

print("=== Testing imports ===")
try:
    import pandas as pd
    print(f"  pandas: {pd.__version__}")
except Exception as e:
    print(f"  pandas FAILED: {e}")

try:
    import pyarrow as pa
    print(f"  pyarrow: {pa.__version__}")
except Exception as e:
    print(f"  pyarrow FAILED: {e}")

try:
    import numpy as np
    print(f"  numpy: {np.__version__}")
except Exception as e:
    print(f"  numpy FAILED: {e}")

try:
    import nfl_data_py as nfl
    print(f"  nfl_data_py: OK (imported)")
    print(f"    file: {nfl.__file__}")
except Exception as e:
    print(f"  nfl_data_py FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

print()
print("=== Testing a tiny data pull (2024 weekly stats, 1 season only) ===")
try:
    df = nfl.import_weekly_data([2024])
    print(f"  SUCCESS: pulled {len(df):,} rows, {len(df.columns)} columns")
    print(f"  Sample columns: {list(df.columns[:10])}")
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()

print()
print("=== Testing IDs import ===")
try:
    ids = nfl.import_ids()
    print(f"  SUCCESS: pulled {len(ids):,} rows")
    sleeper_cols = [c for c in ids.columns if 'sleeper' in c.lower()]
    print(f"  sleeper columns: {sleeper_cols}")
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
