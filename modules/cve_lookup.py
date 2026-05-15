import requests
import queue
import nmap

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def run_cve_lookup(target: str, log_queue: queue.Queue) -> list:
    findings = []

    try:
        log_queue.put(("[INFO]", "Starting CVE lookup — detecting services..."))

        services = _detect_services(target, log_queue)

        if not services:
            log_queue.put(("[INFO]", "No services detected for CVE lookup."))
            return findings

        for service_info in services:
            keyword  = service_info['keyword']
            port     = service_info['port']

            log_queue.put(("[INFO]", f"Looking up CVEs for: {keyword}"))
            cves = _fetch_cves(keyword, log_queue)

            for cve in cves[:3]:  # Max 3 CVEs per service
                cvss = cve.get('cvss', 0.0)
                severity = _cvss_to_severity(cvss)

                findings.append({
                    'title':       f"{cve['id']} — {keyword} (Port {port})",
                    'severity':    severity,
                    'port':        str(port),
                    'description': cve.get('description', 'No description available.'),
                    'remediation': f"Apply latest patches for {keyword}. "
                                   f"Check vendor advisory for {cve['id']}.",
                    'cvss_score':  cvss,
                })
                log_queue.put(("[WARN]",
                    f"CVE found: {cve['id']} CVSS:{cvss} ({severity})"))

        log_queue.put(("[OK]",
            f"CVE lookup complete — {len(findings)} CVEs found."))

    except Exception as e:
        log_queue.put(("[ERR]", f"CVE lookup error: {str(e)}"))

    return findings


def _detect_services(target, log_queue):
    services = []
    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=target, arguments='-sV -T4 --top-ports 100')

        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                for port in nm[host][proto].keys():
                    info    = nm[host][proto][port]
                    product = info.get('product', '')
                    version = info.get('version', '')
                    name    = info.get('name', '')

                    if product:
                        keyword = f"{product} {version}".strip()
                        services.append({'keyword': keyword, 'port': port})
                        log_queue.put(("[INFO]",
                            f"Detected: {keyword} on port {port}"))

    except Exception as e:
        log_queue.put(("[WARN]", f"Service detection failed: {e}"))

    return services


def _fetch_cves(keyword: str, log_queue) -> list:
    cves = []
    try:
        params   = {'keywordSearch': keyword, 'resultsPerPage': 5}
        response = requests.get(NVD_API, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            for item in data.get('vulnerabilities', []):
                cve_data    = item.get('cve', {})
                cve_id      = cve_data.get('id', 'Unknown')
                descriptions = cve_data.get('descriptions', [])
                desc         = next(
                    (d['value'] for d in descriptions if d['lang'] == 'en'),
                    'No description.')

                # Get CVSS score
                cvss = 0.0
                metrics = cve_data.get('metrics', {})
                for key in ['cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2']:
                    if key in metrics and metrics[key]:
                        cvss = metrics[key][0].get(
                            'cvssData', {}).get('baseScore', 0.0)
                        break

                cves.append({'id': cve_id, 'description': desc, 'cvss': cvss})

        else:
            log_queue.put(("[WARN]", f"NVD API returned {response.status_code}"))

    except Exception as e:
        log_queue.put(("[WARN]", f"CVE fetch failed for '{keyword}': {e}"))

    return cves


def _cvss_to_severity(score: float) -> str:
    if score >= 9.0: return 'Critical'
    if score >= 7.0: return 'High'
    if score >= 4.0: return 'Medium'
    if score >= 0.1: return 'Low'
    return 'Info'