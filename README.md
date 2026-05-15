# PyVAF — Python Vulnerability Assessment Framework

A desktop-based vulnerability assessment tool built entirely in Python.
Scans targets for common security weaknesses, correlates findings against
the NVD CVE database, and generates professional PDF reports.

## Features

- Port scanning and service detection (Nmap)
- Web security header analysis
- SSL/TLS certificate and cipher inspection
- DNS reconnaissance (SPF, DMARC, zone transfer)
- CVE lookup via NVD API
- Real-time live log viewer
- Severity scoring based on CVSS v3
- Automatic finding deduplication
- Professional PDF report generation
- Scan history with SQLite persistence
- Modern dark-themed GUI (CustomTkinter)

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| GUI        | CustomTkinter                     |
| Backend    | Flask (REST API)                  |
| Database   | SQLite + SQLAlchemy               |
| Port scan  | python-nmap                       |
| Web scan   | requests, BeautifulSoup4          |
| SSL check  | ssl, cryptography                 |
| DNS recon  | dnspython                         |
| CVE lookup | NVD REST API                      |
| Reports    | fpdf2                             |
| Config     | PyYAML                            |

## Installation

1. Clone the repository:
   git clone https://github.com/yourusername/pyvaf.git
   cd pyvaf

2. Create and activate virtual environment:
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/macOS

3. Install dependencies:
   pip install -r requirements.txt

4. Run the application:
   python main.py

## Usage

1. Open the app — the dashboard shows scan statistics
2. Click New Scan — enter a target IP or domain
3. Select modules — Port, Web, SSL, DNS, CVE
4. Click Start Scan — watch the live log
5. Click Findings — view colour-coded vulnerability table
6. Click Reports — generate and open a PDF report

## Legal Notice

This tool is intended for authorised security testing only.
Only scan targets you have explicit permission to test.
The authors are not responsible for misuse.

## Target for Testing

scanme.nmap.org — a legal public target maintained by Nmap
for testing purposes.

## Project Structure

pyvaf/
├── main.py          Entry point
├── config.yaml      Configuration
├── api/             Flask REST API
├── core/            Scanner, analyzer, reporter
├── gui/             CustomTkinter interface
├── models/          SQLAlchemy database models
├── modules/         Scan modules
└── reports/         Generated PDF reports