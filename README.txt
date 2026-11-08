# Domain Search Browser

A small desktop app for searching publicly indexed pages on a domain you own or are authorized to assess. It builds a domain-scoped Google query and opens it in your default web browser. It does not retrieve or store search results itself.

## Requirements

- Python 3.10 or newer
- Tkinter, which is included with most standard Python installations
- An internet connection and a web browser

The app uses only Python's standard library; no third-party packages are needed to run `hi.py`.

## Run on Windows

Open PowerShell in this folder and run:

```powershell
py osint.py
```

If the `py` command is unavailable, run `python osint.py` instead.

## Use

1. Enter a domain, such as `example.com`.
2. Enter ordinary words to search for and, optionally, an exact phrase.
3. Confirm that you are authorized to assess the domain.
4. Select **Search Google** to open the query in a new browser tab.

Searches are restricted to the supplied domain. Use this tool only for domains you own or have permission to assess.
