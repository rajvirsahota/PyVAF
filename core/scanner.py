import queue
import threading
from datetime import datetime
from models.database import db
from models.scan import Scan
from models.finding import Finding
from modules.port_scan  import run_port_scan
from modules.ssl_check  import run_ssl_check
from modules.web_scan   import run_web_scan
from modules.dns_recon  import run_dns_recon
from modules.cve_lookup import run_cve_lookup

log_queue = queue.Queue()

def run_scan(app, scan_id: int):
    
    with app.app_context():
        scan = Scan.query.get(scan_id)
        if not scan:
            return

        scan.status = 'running'
        db.session.commit()

        modules = scan.modules.split(',') if scan.modules else []
        target  = scan.target
        all_findings = []

        module_map = {
            'port': ('Port Scanner',    run_port_scan),
            'ssl':  ('SSL/TLS Checker', run_ssl_check),
            'web':  ('Web Scanner',     run_web_scan),
            'dns':  ('DNS Recon',       run_dns_recon),
            'cve':  ('CVE Lookup',      run_cve_lookup),
        }

        total    = sum(1 for m in modules if m in module_map)
        complete = 0

        log_queue.put(("[INFO]",
            f"Scan #{scan_id} started on {target} — {total} modules"))

        for module_key in modules:
            if module_key not in module_map:
                continue

            name, func = module_map[module_key]
            log_queue.put(("[INFO]", f"Running {name}..."))

            try:
                findings = func(target, log_queue)
                all_findings.extend(findings)
            except Exception as e:
                log_queue.put(("[ERR]", f"{name} failed: {str(e)}"))

            complete += 1
            progress = int((complete / total) * 100)
            log_queue.put(("[PROGRESS]", str(progress)))

        for f in all_findings:
            finding = Finding(
                scan_id     = scan_id,
                title       = f['title'],
                severity    = f['severity'],
                port        = f.get('port', ''),
                description = f.get('description', ''),
                remediation = f.get('remediation', ''),
                cvss_score  = f.get('cvss_score', 0.0),
            )
            db.session.add(finding)

        scan.status      = 'complete'
        scan.finished_at = datetime.utcnow()
        db.session.commit()

        log_queue.put(("[OK]",
            f"Scan #{scan_id} complete — {len(all_findings)} findings saved."))
        try:
            from core.analyzer import analyze_scan
            result = analyze_scan(app, scan_id)
            log_queue.put(("[INFO]",
                f"Risk score: {result['risk_score']}/10 "
                f"— {result['risk_label']}"))
            if result['duplicates_removed'] > 0:
                log_queue.put(("[INFO]",
                    f"{result['duplicates_removed']} duplicate findings removed."))
        except Exception as e:
            log_queue.put(("[WARN]", f"Analysis error: {e}"))
        log_queue.put(("[DONE]", str(scan_id)))