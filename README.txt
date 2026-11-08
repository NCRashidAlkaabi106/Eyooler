# Eyooler

Eyooler is a Flask-based OSINT search tool for finding relevant information on public web pages. Enter a target or topic, add an optional condition, and optionally limit the search to a website.

## Features

- Search by keyword, company, person, or topic.
- Add an optional condition, such as `phone number`.
- Optionally limit results to a domain.
- Choose Google, Bing, or DuckDuckGo.
- View filtered public results and open the search directly with the selected provider.
- Fall back to DuckDuckGo when the selected provider does not return readable results.

Search providers may limit automated access, so results and availability can vary.

## Requirements

- Python 3.10 or newer
- An internet connection

## Run on Windows

Clone the repository, then run these commands in PowerShell:

```powershell
git clone https://github.com/NCRashidAlkaabi106/Eyooler.git
cd Eyooler
cd "all projects"
py -m venv .venv
python.exe -m pip install -r requirements.txt
python.exe osint.py
