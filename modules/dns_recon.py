import dns.resolver
import dns.zone
import dns.query
import queue

def run_dns_recon(target: str, log_queue: queue.Queue) -> list:
    findings = []

    try:
        log_queue.put(("[INFO]", f"Starting DNS recon on {target}..."))
        hostname = target.replace("https://","").replace("http://","").split("/")[0]

        # A Records
        findings += _check_record(hostname, 'A', log_queue)

        # MX Records
        findings += _check_record(hostname, 'MX', log_queue)

        # TXT Records (SPF/DMARC)
        findings += _check_txt_records(hostname, log_queue)

        # Zone Transfer attempt
        findings += _check_zone_transfer(hostname, log_queue)

        log_queue.put(("[OK]", f"DNS recon complete — {len(findings)} issues found."))

    except Exception as e:
        log_queue.put(("[ERR]", f"DNS recon error: {str(e)}"))

    return findings


def _check_record(hostname, record_type, log_queue):
    findings = []
    try:
        answers = dns.resolver.resolve(hostname, record_type)
        for r in answers:
            log_queue.put(("[OK]", f"{record_type} record: {r}"))
    except dns.resolver.NXDOMAIN:
        log_queue.put(("[WARN]", f"Domain {hostname} does not exist (NXDOMAIN)"))
    except dns.resolver.NoAnswer:
        log_queue.put(("[INFO]", f"No {record_type} records found for {hostname}"))
    except Exception as e:
        log_queue.put(("[WARN]", f"{record_type} lookup failed: {e}"))
    return findings


def _check_txt_records(hostname, log_queue):
    findings = []
    try:
        answers  = dns.resolver.resolve(hostname, 'TXT')
        txt_data = [r.to_text() for r in answers]
        has_spf   = any('v=spf1'   in t for t in txt_data)
        has_dmarc = any('v=DMARC1' in t for t in txt_data)

        if not has_spf:
            log_queue.put(("[WARN]", "No SPF record found — email spoofing possible"))
            findings.append({
                'title':       'Missing SPF Record',
                'severity':    'Medium',
                'port':        'DNS',
                'description': 'No SPF TXT record found. Attackers can spoof '
                               'emails from this domain.',
                'remediation': 'Add an SPF record: v=spf1 include:yourmailserver.com ~all',
                'cvss_score':  5.0,
            })
        else:
            log_queue.put(("[OK]", "SPF record found"))

        if not has_dmarc:
            log_queue.put(("[WARN]", "No DMARC record found"))
            findings.append({
                'title':       'Missing DMARC Record',
                'severity':    'Medium',
                'port':        'DNS',
                'description': 'No DMARC policy found. Without DMARC, '
                               'phishing attacks are easier.',
                'remediation': 'Add a DMARC record: _dmarc.yourdomain.com TXT '
                               '"v=DMARC1; p=reject; rua=mailto:admin@yourdomain.com"',
                'cvss_score':  4.0,
            })
        else:
            log_queue.put(("[OK]", "DMARC record found"))

    except Exception as e:
        log_queue.put(("[WARN]", f"TXT record lookup failed: {e}"))

    return findings


def _check_zone_transfer(hostname, log_queue):
    findings = []
    try:
        ns_records = dns.resolver.resolve(hostname, 'NS')
        for ns in ns_records:
            ns_host = str(ns).rstrip('.')
            try:
                zone = dns.zone.from_xfr(
                    dns.query.xfr(ns_host, hostname, timeout=5))
                if zone:
                    log_queue.put(("[ERR]",
                        f"Zone transfer ALLOWED on {ns_host} — critical!"))
                    findings.append({
                        'title':       f'DNS Zone Transfer Allowed ({ns_host})',
                        'severity':    'Critical',
                        'port':        'DNS/53',
                        'description': f'The nameserver {ns_host} allows zone '
                                       'transfers, exposing all DNS records.',
                        'remediation': 'Restrict zone transfers to authorised '
                                       'secondary nameservers only.',
                        'cvss_score':  9.0,
                    })
            except Exception:
                log_queue.put(("[OK]", f"Zone transfer blocked on {ns_host}"))

    except Exception as e:
        log_queue.put(("[WARN]", f"Zone transfer check failed: {e}"))

    return findings