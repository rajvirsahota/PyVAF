from fpdf import FPDF
from datetime import datetime
from models.scan import Scan
from models.finding import Finding
import os

def sanitize(text: str) -> str:
    """Remove or replace characters unsupported by fpdf2 Helvetica."""
    if not text:
        return ''
    replacements = {
        '\u2014': '-',   # em dash —
        '\u2013': '-',   # en dash –
        '\u2018': "'",   # left single quote '
        '\u2019': "'",   # right single quote '
        '\u201c': '"',   # left double quote "
        '\u201d': '"',   # right double quote "
        '\u2022': '*',   # bullet •
        '\u2026': '...', # ellipsis …
        '\u00e9': 'e',   # é
        '\u00e0': 'a',   # à
        '\u00fc': 'u',   # ü
        '\u00f6': 'o',   # ö
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Remove any remaining non-latin characters
    return text.encode('latin-1', errors='replace').decode('latin-1')

SEVERITY_COLORS = {
    'Critical': (240, 149, 149),
    'High':     (250, 199, 117),
    'Medium':   (151, 196, 89),
    'Low':      (133, 183, 235),
    'Info':     (139, 141, 158),
}

class VAFReport(FPDF):

    def header(self):
        self.set_fill_color(26, 27, 38)
        self.rect(0, 0, 210, 20, 'F')
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(167, 139, 250)
        self.set_xy(10, 5)
        self.cell(0, 10, 'PyVAF - Vulnerability Assessment Report', align='L')
        self.set_font('Helvetica', '', 9)
        self.set_text_color(139, 141, 158)
        self.set_xy(0, 5)
        self.cell(200, 10,
            datetime.now().strftime('%Y-%m-%d %H:%M'), align='R')
        self.ln(18)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(139, 141, 158)
        self.cell(0, 10,
            f'Page {self.page_no()} | PyVAF Vulnerability Assessment Framework',
            align='C')

    def section_title(self, title: str):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(167, 139, 250)
        self.set_fill_color(37, 38, 56)
        self.cell(0, 10, f'  {title}', ln=True, fill=True)
        self.ln(3)

    def key_value(self, key: str, value: str,
                  key_color=(139,141,158), val_color=(201,204,214)):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*key_color)
        self.cell(50, 7, key)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*val_color)
         # sanitize value here
        safe_value = sanitize(str(value))
        self.cell(0, 7, str(value), ln=True)


def generate_report(app, scan_id: int) -> str:
    """Generate PDF report and return file path."""

    with app.app_context():
        scan     = Scan.query.get(scan_id)
        findings = Finding.query.filter_by(
            scan_id=scan_id).order_by(
            Finding.cvss_score.desc()).all()

        if not scan:
            raise ValueError(f"Scan #{scan_id} not found.")

        # Count by severity
        summary = {'Critical':0,'High':0,'Medium':0,'Low':0,'Info':0}
        for f in findings:
            if f.severity in summary:
                summary[f.severity] += 1

        # Risk score
        weights   = {'Critical':10,'High':7,'Medium':4,'Low':1,'Info':0}
        total_w   = sum(weights.get(f.severity,0) for f in findings)
        max_w     = len(findings) * 10 if findings else 1
        risk_score = round((total_w / max_w) * 10, 1)

        if risk_score >= 8:   risk_label = 'Critical Risk'
        elif risk_score >= 6: risk_label = 'High Risk'
        elif risk_score >= 4: risk_label = 'Medium Risk'
        elif risk_score >= 2: risk_label = 'Low Risk'
        else:                 risk_label = 'Minimal Risk'

        pdf = VAFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # ── COVER SECTION ──────────────────────────────────────
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(201, 204, 214)
        pdf.ln(4)
        pdf.cell(0, 12, 'Vulnerability Assessment Report', ln=True)

        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(139, 141, 158)
        pdf.cell(0, 8, f'Target: {scan.target}', ln=True)
        pdf.ln(6)

        # Risk score badge
        r, g, b = {
            'Critical Risk': (240,149,149),
            'High Risk':     (250,199,117),
            'Medium Risk':   (151,196, 89),
            'Low Risk':      (133,183,235),
            'Minimal Risk':  (139,141,158),
        }.get(risk_label, (139,141,158))

        pdf.set_fill_color(37, 38, 56)
        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(0.8)
        pdf.rect(10, pdf.get_y(), 90, 22, 'DF')
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(r, g, b)
        pdf.set_xy(10, pdf.get_y() + 3)
        pdf.cell(90, 8, f'Risk Score: {risk_score}/10', align='C', ln=False)
        pdf.set_xy(105, pdf.get_y())
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(90, 8, risk_label, align='L')
        pdf.ln(28)

        # ── SCAN DETAILS ───────────────────────────────────────
        pdf.section_title('Scan Details')
        pdf.key_value('Target:',     sanitize(scan.target))
        pdf.key_value('Scan ID:',    f'#{scan.id}')
        pdf.key_value('Status:',     sanitize(scan.status.capitalize()))
        pdf.key_value('Started:',    str(scan.started_at)[:19])
        pdf.key_value('Finished:',
            str(scan.finished_at)[:19] if scan.finished_at else 'N/A')
        pdf.key_value('Modules:',sanitize(
            ', '.join(scan.modules.split(',')) if scan.modules else 'N/A'))
        pdf.key_value('Total Findings:', str(len(findings)))
        pdf.ln(6)

        # ── SEVERITY SUMMARY ───────────────────────────────────
        pdf.section_title('Severity Summary')

        col_w = 35
        for sev, count in summary.items():
            r2, g2, b2 = SEVERITY_COLORS[sev]
            pdf.set_fill_color(37, 38, 56)
            pdf.set_draw_color(r2, g2, b2)
            pdf.set_line_width(0.5)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.rect(x, y, col_w, 18, 'DF')
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(r2, g2, b2)
            pdf.set_xy(x, y + 2)
            pdf.cell(col_w, 6, sev, align='C')
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_xy(x, y + 8)
            pdf.cell(col_w, 8, str(count), align='C')
            pdf.set_xy(x + col_w + 2, y)

        pdf.ln(26)

        # ── EXECUTIVE SUMMARY ──────────────────────────────────
        pdf.section_title('Executive Summary')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(201, 204, 214)

        crit_count = summary['Critical']
        high_count = summary['High']

        summary_text = (
            f"A vulnerability assessment was conducted against {scan.target} "
            f"using the PyVAF framework. The scan identified {len(findings)} "
            f"security findings across {len(scan.modules.split(','))} scanning "
            f"modules. The overall risk score is {risk_score}/10 "
            f"({risk_label}). "
        )

        if crit_count > 0:
            summary_text += (
                f"There are {crit_count} critical severity findings that "
                f"require immediate attention. "
            )
        if high_count > 0:
            summary_text += (
                f"{high_count} high severity findings were also identified "
                f"and should be remediated as a priority. "
            )

        summary_text += (
            "Detailed findings with remediation guidance are provided "
            "in the sections below."
        )

        pdf.multi_cell(0, 6, sanitize(summary_text))
        pdf.ln(6)

        # ── FINDINGS TABLE ─────────────────────────────────────
        pdf.section_title(f'Detailed Findings ({len(findings)})')

        if not findings:
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(139, 141, 158)
            pdf.cell(0, 8, 'No findings recorded for this scan.', ln=True)
        else:
            # Table header
            pdf.set_fill_color(37, 38, 56)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(139, 141, 158)
            pdf.set_draw_color(42, 43, 61)
            pdf.set_line_width(0.3)

            col_widths = [22, 90, 22, 18, 38]
            headers    = ['Severity','Title','Port','CVSS','Module']

            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 8, h,
                         border=1, fill=True, align='C')
            pdf.ln()

            # Table rows
            for f in findings:
                if pdf.get_y() > 260:
                    pdf.add_page()

                r3, g3, b3 = SEVERITY_COLORS.get(
                    f.severity, (139,141,158))

                # Severity cell (colored)
                pdf.set_fill_color(37, 38, 56)
                pdf.set_draw_color(42, 43, 61)
                pdf.set_font('Helvetica', 'B', 8)
                pdf.set_text_color(r3, g3, b3)
                pdf.cell(col_widths[0], 7, f.severity,
                         border=1, fill=True, align='C')

                # Title
                pdf.set_font('Helvetica', '', 8)
                pdf.set_text_color(201, 204, 214)
                title = f.title[:55] + '. . .' if len(f.title) > 55 else f.title
                pdf.cell(col_widths[1], 7, sanitize(title), border=1, fill=True)

                # Port
                pdf.set_text_color(139, 141, 158)
                pdf.cell(col_widths[2], 7,
                         str(f.port or 'N/A'), border=1,
                         fill=True, align='C')

                # CVSS
                pdf.set_text_color(r3, g3, b3)
                pdf.cell(col_widths[3], 7,
                         str(f.cvss_score), border=1,
                         fill=True, align='C')

                # Module (derived from port)
                pdf.set_text_color(139, 141, 158)
                pdf.set_font('Helvetica', '', 7)
                pdf.cell(col_widths[4], 7,
                         '-', border=1, fill=True, align='C')
                pdf.ln()

            pdf.ln(6)

        # ── REMEDIATION DETAILS ────────────────────────────────
        critical_and_high = [
            f for f in findings
            if f.severity in ('Critical', 'High')
        ]

        if critical_and_high:
            pdf.add_page()
            pdf.section_title('Remediation Details - Critical & High')

            for f in critical_and_high:
                if pdf.get_y() > 240:
                    pdf.add_page()

                r4, g4, b4 = SEVERITY_COLORS.get(
                    f.severity, (139,141,158))

                # Finding title bar
                pdf.set_fill_color(37, 38, 56)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(r4, g4, b4)
                pdf.cell(0, 8,sanitize(
                    f'  [{f.severity}] {f.title[:70]}'),
                    ln=True, fill=True)

                # Description
                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_text_color(139, 141, 158)
                pdf.cell(0, 6, 'Description:', ln=True)
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(201, 204, 214)
                pdf.multi_cell(0, 5,sanitize(
                    f.description or 'No description available.'))

                # Remediation
                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_text_color(139, 141, 158)
                pdf.cell(0, 6, 'Remediation:', ln=True)
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(151, 196, 89)
                pdf.multi_cell(0, 5,sanitize(
                    f.remediation or 'No remediation available.'))
                pdf.ln(4)

        # ── SAVE FILE ──────────────────────────────────────────
        os.makedirs('reports', exist_ok=True)
        filename  = (f"reports/pyvaf_report_scan{scan_id}_"
                     f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        pdf.output(filename)
        return filename