# Validation of textile electrodes for FES application

Mini reproducible demo for Elastatrode™ textile electrode validation.

## What is in this repo
- `project_sheet.pdf` — one-page project summary (high-level, non-sensitive).
- `analysis.py` — Python script that parses selected LCR CSVs, computes per-frequency averages, and generates two figures.
- `Data/` — selected CSV exports from the LCR-6300 used in the demo (only a small, representative subset).


## How to run (local)
1. Install Python 3.8+.
2. Create a virtual environment and activate it:
   - Windows (PowerShell):
     ```
     python -m venv .env
     .\.env\Scripts\Activate.ps1
     ```
   - macOS / Linux:
     ```
     python3 -m venv .env
     source .env/bin/activate
     ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the analysis:
   ```
   python analysis.py
   ```
5. Outputs:
   - Figures: `figures/`
   - Processed CSVs: `processed/`

## Notes on data and privacy
- This repo contains a *small, representative subset* of measurement CSVs used for demonstration.
- Do NOT upload raw patient-identifiable data or sensitive clinical records to this public repo.
- If you need the full dataset or the full thesis, contact me — I can produce an anonymized / sanitized export suitable for sharing.

## License
MIT
