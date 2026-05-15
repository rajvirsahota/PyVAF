import nmap
import queue

def run_port_scan(target: str, log_queue: queue.Queue) -> list:
    findings = []

    try:
        log_queue.put(("[INFO]", f"Starting port scan on {target}..."))
        nm = nmap.PortScanner()
        nm.scan(hosts=target, arguments='-sV -T4 --top-ports 1000')

        for host in nm.all_hosts():
            log_queue.put(("[INFO]", f"Host: {host} ({nm[host].hostname()})"))

            for proto in nm[host].all_protocols():
                ports = nm[host][proto].keys()

                for port in sorted(ports):
                    state   = nm[host][proto][port]['state']
                    service = nm[host][proto][port]['name']
                    version = nm[host][proto][port]['version']
                    product = nm[host][proto][port]['product']

                    if state == 'open':
                        full_service = f"{product} {version}".strip() or service
                        log_queue.put(("[OK]",
                            f"Open port {port}/{proto} — {full_service}"))

                        severity = _assess_port_severity(port, service)
                        findings.append({
                            'title':       f"Open port {port} — {full_service}",
                            'severity':    severity,
                            'port':        str(port),
                            'description': f"Port {port}/{proto} is open "
                                           f"running {full_service}.",
                            'remediation': _get_remediation(port, service),
                            'cvss_score':  _get_cvss(severity),
                        })

        log_queue.put(("[OK]", f"Port scan complete — {len(findings)} open ports found."))

    except Exception as e:
        log_queue.put(("[ERR]", f"Port scan error: {str(e)}"))

    return findings


def _assess_port_severity(port: int, service: str) -> str:
    critical_ports = {21, 23, 445, 3389, 5900}
    high_ports     = {22, 25, 110, 143, 3306, 5432, 6379, 27017}
    medium_ports   = {80, 8080, 8443, 8888}

    if port in critical_ports:
        return 'Critical'
    elif port in high_ports:
        return 'High'
    elif port in medium_ports:
        return 'Medium'
    elif port == 443:
        return 'Info'
    else:
        return 'Low'


def _get_remediation(port: int, service: str) -> str:
    remediations = {
        21:    "Disable FTP — use SFTP instead. FTP transmits credentials in plaintext.",
        22:    "Restrict SSH access by IP. Disable root login. Use key-based auth.",
        23:    "Disable Telnet immediately — use SSH instead.",
        25:    "Restrict SMTP relay. Enable authentication.",
        80:    "Redirect HTTP to HTTPS. Avoid serving sensitive content over HTTP.",
        443:   "Ensure TLS 1.2+ is enforced. Check certificate validity.",
        445:   "Disable SMB if not needed. Apply all Windows patches (EternalBlue).",
        3306:  "Restrict MySQL to localhost or VPN only. Disable remote root login.",
        3389:  "Restrict RDP by IP. Enable NLA. Use VPN for remote access.",
        5432:  "Restrict PostgreSQL to localhost. Use strong passwords.",
        5900:  "Disable VNC or restrict by IP and use strong passwords.",
        6379:  "Require Redis authentication. Never expose Redis to the internet.",
        27017: "Enable MongoDB authentication. Restrict to localhost.",
    }
    return remediations.get(port,
        f"Review whether port {port} needs to be publicly accessible. "
        "Close unnecessary ports.")


def _get_cvss(severity: str) -> float:
    return {'Critical': 9.0, 'High': 7.0,
            'Medium': 5.0, 'Low': 3.0, 'Info': 0.0}.get(severity, 0.0)