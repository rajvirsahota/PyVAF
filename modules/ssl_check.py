import ssl
import socket
import queue
from datetime import datetime

def run_ssl_check(target: str, log_queue: queue.Queue) -> list:
    findings = []

    try:
        log_queue.put(("[INFO]", f"Starting SSL/TLS check on {target}..."))
        hostname = target.replace("https://", "").replace("http://", "").split("/")[0]

        context = ssl.create_default_context()

        try:
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    tls_version = ssock.version()

                    log_queue.put(("[OK]", f"Connected via {tls_version}"))

                    # Check certificate expiry
                    findings += _check_expiry(cert, hostname, log_queue)

                    # Check TLS version
                    findings += _check_tls_version(tls_version, log_queue)

                    # Check cipher
                    cipher = ssock.cipher()
                    findings += _check_cipher(cipher, log_queue)

        except ssl.SSLCertVerificationError:
            log_queue.put(("[WARN]", "SSL certificate verification failed — self-signed?"))
            findings.append({
                'title':       'SSL Certificate Verification Failed',
                'severity':    'High',
                'port':        '443',
                'description': 'The SSL certificate could not be verified. '
                               'It may be self-signed or from an untrusted CA.',
                'remediation': 'Install a valid certificate from a trusted CA '
                               '(e.g. Let\'s Encrypt).',
                'cvss_score':  7.0,
            })

        except (ConnectionRefusedError, socket.timeout, OSError):
            log_queue.put(("[WARN]", f"Port 443 not reachable on {hostname} — skipping SSL check."))

        log_queue.put(("[OK]", f"SSL check complete — {len(findings)} issues found."))

    except Exception as e:
        log_queue.put(("[ERR]", f"SSL check error: {str(e)}"))

    return findings


def _check_expiry(cert, hostname, log_queue):
    findings = []
    try:
        expire_str = cert['notAfter']
        expire_dt  = datetime.strptime(expire_str, '%b %d %H:%M:%S %Y %Z')
        days_left  = (expire_dt - datetime.utcnow()).days

        if days_left < 0:
            log_queue.put(("[ERR]", f"Certificate EXPIRED {abs(days_left)} days ago!"))
            findings.append({
                'title':       f'SSL Certificate Expired ({abs(days_left)} days ago)',
                'severity':    'Critical',
                'port':        '443',
                'description': f'Certificate expired on {expire_str}.',
                'remediation': 'Renew the SSL certificate immediately.',
                'cvss_score':  9.0,
            })
        elif days_left < 30:
            log_queue.put(("[WARN]", f"Certificate expires in {days_left} days!"))
            findings.append({
                'title':       f'SSL Certificate Expiring Soon ({days_left} days)',
                'severity':    'High',
                'port':        '443',
                'description': f'Certificate expires on {expire_str}.',
                'remediation': 'Renew the SSL certificate before it expires.',
                'cvss_score':  7.0,
            })
        else:
            log_queue.put(("[OK]", f"Certificate valid for {days_left} more days."))

    except Exception as e:
        log_queue.put(("[WARN]", f"Could not parse cert expiry: {e}"))

    return findings


def _check_tls_version(version, log_queue):
    findings = []
    weak_versions = {'TLSv1': 'High', 'TLSv1.1': 'Medium', 'SSLv2': 'Critical', 'SSLv3': 'Critical'}

    if version in weak_versions:
        severity = weak_versions[version]
        log_queue.put(("[WARN]", f"Weak TLS version in use: {version}"))
        findings.append({
            'title':       f'Deprecated TLS Version: {version}',
            'severity':    severity,
            'port':        '443',
            'description': f'The server supports {version} which is deprecated and insecure.',
            'remediation': 'Disable TLS 1.0 and 1.1. Enforce TLS 1.2 or TLS 1.3 only.',
            'cvss_score':  7.0 if severity == 'High' else 5.0,
        })
    else:
        log_queue.put(("[OK]", f"TLS version OK: {version}"))

    return findings


def _check_cipher(cipher, log_queue):
    findings = []
    if cipher:
        cipher_name = cipher[0]
        weak_ciphers = ['RC4', 'DES', 'NULL', 'EXPORT', 'MD5']
        for weak in weak_ciphers:
            if weak in cipher_name.upper():
                log_queue.put(("[WARN]", f"Weak cipher detected: {cipher_name}"))
                findings.append({
                    'title':       f'Weak Cipher Suite: {cipher_name}',
                    'severity':    'High',
                    'port':        '443',
                    'description': f'The server is using weak cipher: {cipher_name}.',
                    'remediation': 'Disable weak ciphers. Use AES-256-GCM or CHACHA20.',
                    'cvss_score':  7.0,
                })
                return findings
        log_queue.put(("[OK]", f"Cipher suite OK: {cipher_name}"))
    return findings