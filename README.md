# Demographic Analysis Tool

This repository contains a Streamlit application for analyzing demographic data.

## Running Locally

1. **Create and activate a Python 3.11+ environment.**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies.**
   Install the packages listed in `pyproject.toml`:
   ```bash
   pip install numpy>=2.3.1 openai>=1.90.0 openpyxl>=3.1.5 pandas>=2.3.0 \
              plotly>=6.1.2 psycopg2-binary>=2.9.10 scipy>=1.16.0 \
              sqlalchemy>=2.0.41 streamlit>=1.46.0 xlsxwriter>=3.2.5
   ```

   Alternatively, generate a `requirements.txt` from `pyproject.toml` and use
   `pip install -r requirements.txt`.

3. **Run the Streamlit app.**
   ```bash
   streamlit run app.py
   ```
   The application will be available in your browser at the URL printed by
   Streamlit (usually `http://localhost:8501`).

## Notes

- The app uses optional database features controlled via the `DATABASE_URL`
  environment variable. If not set, the application runs in memory-only mode.
- Static assets live in `static/`, and helper modules are in `utils/`.
