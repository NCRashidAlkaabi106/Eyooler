# Eyooler OSINT Search

Eyooler is a small Flask app for searching public web results by target/topic, optional information condition, and optional site limit.

## Requirements

- Python 3.10 or newer
- Packages listed in `requirements.txt`
- An internet connection

## Run on Windows

Open PowerShell in this folder and run:

```powershell
py -m pip install -r requirements.txt
py osint.py
```

The app opens at `http://127.0.0.1:5000`.

## Search behavior

The target is placed first, followed by the optional condition and site limit. The app searches publicly available results and filters them for relevance. Search providers may restrict automated result fetching; when that happens, Eyooler tries DuckDuckGo and provides a link to run the search directly in the selected provider.

Eyooler does not support searches for passwords, credentials, access tokens, API keys, or private account access.