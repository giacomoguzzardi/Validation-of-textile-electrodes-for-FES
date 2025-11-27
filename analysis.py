# analysis.py

import sys
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
except Exception as e:
    print("IMPORT ERROR:", e)
    print("\nYou need numpy, pandas and matplotlib. Install them by running this in a Windows command prompt:\n")
    print("    pip install numpy pandas matplotlib\n")
    sys.exit(1)

# --- folders & freq vector ---
ROOT2 = Path('.').resolve()
ROOT = ROOT2 / 'Downloads' / 'FES_folder'
DATA_DIR = ROOT / 'data'
FIG_DIR = ROOT / 'figures'
PROCESSED_DIR = ROOT / 'processed'

for d in (DATA_DIR, FIG_DIR, PROCESSED_DIR):
    d.mkdir(exist_ok=True)

freq = np.arange(10, 101, 10)  # [10,20,...,100]
print("Project root:", ROOT)
print("Data folder:", DATA_DIR)
print("Figures will go to:", FIG_DIR)
print("Processed CSVs will go to:", PROCESSED_DIR)

# --- list of files to load (edit here only if you want different names) ---
TO_LOAD = [
    'LIST0423.CSV',  # hydrogel baseline (you pasted)
    'LIST0424.CSV',  # electrode after wash (you pasted)
    'LIST0009.CSV',  # textile baseline (used in scripts)
    'LIST0022.CSV',  # washing cycle example (2)
    'LIST0032.CSV',  # washing cycle example (4/6...) adjust if names differ
    'LIST0042.CSV',  # washing cycle example
    'LIST0052.CSV',  # washing cycle example
    'LIST0096.CSV'   # washing cycle example
]

# --- robust LCR-6300 CSV parser ---
def read_lcr_csv_lcr6300(path: Path, num_freq: int = 10, trim_first_n: int = None, col_name='Z(OHM)', fallback_col_index=2, scale=1e-3):
    """
    Parse LCR-6300 LISTxxxx.CSV files like in your examples:
    - finds header with 'Z(OHM)' and reads subsequent lines starting with '+' or digits
    - extracts the numeric column (Z(OHM)) and reshapes into (num_freq x repeats) to average
    - returns a 1D numpy array of length num_freq in kOhm (scale default 1e-3)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf8', errors='ignore') as f:
        lines = [ln.rstrip('\n') for ln in f]

    # find header line (where columns are listed)
    header_idx = None
    for i, ln in enumerate(lines[:40]):
        if col_name in ln:
            header_idx = i
            break

    # collect candidate data lines
    data_lines = []
    if header_idx is not None:
        for ln in lines[header_idx + 1:]:
            if not ln.strip():
                continue
            # accept lines that start with '+' or a digit or '-'
            first = ln.strip()[0]
            if first in ('+',) or first.isdigit() or first == '-':
                data_lines.append(ln)
    else:
        # fallback: take lines that start with '+'
        for ln in lines:
            if ln.strip().startswith('+'):
                data_lines.append(ln)

    if not data_lines:
        raise ValueError(f"No data lines found in {path.name}")

    # decide column index, using header if possible
    col_index = fallback_col_index
    if header_idx is not None:
        cols = [c.strip().strip('"') for c in lines[header_idx].split(',')]
        if col_name in cols:
            col_index = cols.index(col_name)

    values = []
    for ln in data_lines:
        parts = [p.strip().strip('"') for p in ln.split(',')]
        if len(parts) <= col_index:
            continue
        valstr = parts[col_index]
        # try to parse float (handle formats like +3.15453E+04)
        try:
            v = float(valstr)
        except Exception:
            try:
                v = float(valstr.replace('+',''))
            except Exception:
                continue
        values.append(v)

    if not values:
        raise ValueError(f"No numeric impedance values parsed in {path.name}")

    # reshape into (num_freq, repeats)
    ncols = len(values) // num_freq
    if ncols == 0:
        if trim_first_n is not None:
            values = values[:trim_first_n]
            ncols = len(values) // num_freq
        if ncols == 0:
            raise ValueError(f"Not enough rows to reshape for {path.name} (len={len(values)}, num_freq={num_freq})")
    values = values[:ncols * num_freq]
    mat = np.array(values).reshape((ncols, num_freq)).T  # shape (num_freq, ncols)
    avg = mat.mean(axis=1) * scale
    return avg

# --- load the selected files ---
loaded = {}
for fn in TO_LOAD:
    p = DATA_DIR / fn
    if not p.exists():
        print("NOT FOUND (skipped):", fn)
        continue
    try:
        avg = read_lcr_csv_lcr6300(p, num_freq=10, trim_first_n=100, col_name='Z(OHM)', fallback_col_index=2, scale=1e-3)
        loaded[fn] = avg
        print("Loaded:", fn)
    except Exception as e:
        print("Error reading", fn, ":", e)

if not loaded:
    print("\nNo real files were loaded. The script will generate synthetic demo data instead.")
    base = 20 + 0.3 * freq
    loaded = {
        'demo_baseline': base,
        'demo_postwash': base * 1.25,
        'demo_hydrogel': base * 0.9
    }

# --- save processed CSVs and print a short table ---
for name, vec in loaded.items():
    out = pd.DataFrame({'frequency_hz': freq, 'impedance_kohm': vec})
    out_fn = PROCESSED_DIR / f"{Path(name).stem}_processed.csv"
    out.to_csv(out_fn, index=False)
    print("Saved processed:", out_fn.name)

# --- Plot 1: hydrogel vs a selected textile (if hydrogel present) ---
plt.figure(figsize=(6,4))
# plot hydrogel-like entries first
plotted = set()
for k, v in loaded.items():
    if 'hydro' in k.lower():
        plt.plot(freq, v, '-o', linewidth=2, label=k)
        plotted.add(k)
# then plot the rest (textile)
for k, v in loaded.items():
    if k in plotted:
        continue
    plt.plot(freq, v, '-s', linewidth=1.6, label=k)
plt.xlabel('Frequency [Hz]')
plt.ylabel('Impedance [kΩ]')
plt.title('Hydrogel vs textile (selected files)')
plt.grid(True, linestyle='--', alpha=0.3)
plt.legend(fontsize='small')
plt.tight_layout()
fig1 = FIG_DIR / 'hydrogel_vs_textile.png'
plt.savefig(fig1)
print("Saved figure:", fig1.name)
plt.show()

# --- Plot 2: normalized impedance relative to baseline (first loaded item) ---
baseline_key = next(iter(loaded.keys()))
baseline = loaded[baseline_key]
plt.figure(figsize=(7,4))
for k, v in loaded.items():
    plt.plot(freq, v / baseline, marker='o', label=k)
plt.xlabel('Frequency [Hz]')
plt.ylabel(f'Normalized impedance (relative to {baseline_key})')
plt.title('Normalized impedance across files')
plt.ylim([0.4, 1.8])
plt.legend(fontsize='small', ncol=2)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
fig2 = FIG_DIR / 'normalized_impedance.png'
plt.savefig(fig2)
print("Saved figure:", fig2.name)
plt.show()

print("\nDone. Check the 'processed' and 'figures' folders for outputs.")
