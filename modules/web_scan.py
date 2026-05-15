import requests
import queue
from bs4 import BeautifulSoup

SECURITY_HEADERS = {
    'Content-Security-Policy':   ('High',   'Prevents XSS and injection attacks.'),
    'X-Frame-Options':           ('Medium', 'Prevents clickjacking attacks.'),
    'X-Content-Type-Options':    ('Medium', 'Prevents MIME sniffing attacks.'),
    'Strict-Transport-Security': ('High',   'Enforces HTTPS connections.'),
    'Referrer-Policy':           ('Low',    'Controls referrer information leakage.'),
    'Permissions-Policy':        ('Low',    'Controls browser feature access.'),
}

def run_web_scan(target: str, log_queue: queue.Queue) -> list:
    findings = []

    try:
        log_queue.put(("[INFO]", f"Starting web scan on {target}..."))

        if not target.startswith('http'):
            urls = [f"http://{target}", f"https://{target}"]
        else:
            urls = [target]

        for url in urls:
            try:
                response = requests.get(url, timeout=10,
                                        allow_redirects=True,
                                        verify=False)
                log_queue.put(("[OK]", f"Connected to {url} — HTTP {response.status_code}"))

                findings += _check_headers(response, url, log_queue)
                findings += _check_server_disclosure(response, log_queue)
                findings += _check_directory_listing(response, log_queue)
                break

            except requests.exceptions.SSLError:
                log_queue.put(("[WARN]", f"SSL error on {url} — trying next..."))
            except requests.exceptions.ConnectionError:
                log_queue.put(("[WARN]", f"Cannot connect to {url}"))

        log_queue.put(("[OK]", f"Web scan complete — {len(findings)} issues found."))

    except Exception as e:
        log_queue.put(("[ERR]", f"Web scan error: {str(e)}"))

    return findings


def _check_headers(response, url, log_queue):
    findings = []
    for header, (severity, description) in SECURITY_HEADERS.items():
        if header not in response.headers:
            log_queue.put(("[WARN]", f"Missing header: {header}"))
            findings.append({
                'title':       f'Missing Security Header: {header}',
                'severity':    severity,
                'port':        'HTTP',
                'description': f'The response is missing the {header} header. {description}',
                'remediation': f'Add the {header} header to all HTTP responses.',
                'cvss_score':  5.0 if severity == 'High' else 3.0,
            })
        else:
            log_queue.put(("[OK]", f"Header present: {header}"))
    return findings


def _check_server_disclosure(response, log_queue):
    findings = []
    server = response.headers.get('Server', '')
    x_powered = response.headers.get('X-Powered-By', '')

    if server:
        log_queue.put(("[WARN]", f"Server version disclosed: {server}"))
        findings.append({
            'title':       f'Server Version Disclosed: {server}',
            'severity':    'Low',
            'port':        'HTTP',
            'description': f'The Server header reveals: {server}. '
                           'This helps attackers identify software versions.',
            'remediation': 'Remove or obscure the Server header in web server config.',
            'cvss_score':  3.0,
        })

    if x_powered:
        log_queue.put(("[WARN]", f"X-Powered-By disclosed: {x_powered}"))
        findings.append({
            'title':       f'Technology Disclosed: {x_powered}',
            'severity':    'Low',
            'port':        'HTTP',
            'description': f'X-Powered-By header reveals: {x_powered}.',
            'remediation': 'Remove the X-Powered-By header.',
            'cvss_score':  2.0,
        })

    return findings


def _check_directory_listing(response, log_queue):
    findings = []
    indicators = ['Index of /', 'Directory listing for', 'Parent Directory']

    for indicator in indicators:
        if indicator.lower() in response.text.lower():
            log_queue.put(("[ERR]", "Directory listing is enabled!"))
            findings.append({
                'title':       'Directory Listing Enabled',
                'severity':    'Medium',
                'port':        'HTTP',
                'description': 'The web server exposes directory contents, '
                               'revealing sensitive file paths.',
                'remediation': 'Disable directory listing in your web server config.',
                'cvss_score':  5.0,
            })
            break

    return findings