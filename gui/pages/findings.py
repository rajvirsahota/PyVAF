import customtkinter as ctk
import requests
from gui.theme import COLORS

SEVERITY_COLORS = {
    'Critical': '#f09595',
    'High':     '#FAC775',
    'Medium':   '#97C459',
    'Low':      '#85B7EB',
    'Info':     '#8b8d9e',
}

class FindingsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"])
        self.scan_id = None
        self._build_ui()

    def _build_ui(self):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 4))

        ctk.CTkLabel(header, text="Findings",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            header, text="⟳  Refresh",
            width=110, height=34,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._load_findings
        )
        self.refresh_btn.pack(side="right")

        # Scan selector
        selector = ctk.CTkFrame(self, fg_color="transparent")
        selector.pack(fill="x", padx=30, pady=(0, 12))

        ctk.CTkLabel(selector, text="Scan ID:",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(0, 8))

        self.scan_entry = ctk.CTkEntry(
            selector, width=80, height=34,
            placeholder_text="e.g. 1",
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"]
        )
        self.scan_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            selector, text="Load", width=80, height=34,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._load_findings
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(
            selector, text="",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_muted"]
        )
        self.status_label.pack(side="left", padx=12)

        # Summary bar
        self.summary_frame = ctk.CTkFrame(
            self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=30, pady=(0, 12))

        self.summary_labels = {}
        for sev in ['Critical', 'High', 'Medium', 'Low', 'Info']:
            col = SEVERITY_COLORS[sev]
            f = ctk.CTkFrame(self.summary_frame,
                fg_color=COLORS["bg_card"], corner_radius=8)
            f.pack(side="left", padx=(0, 8), ipadx=12, ipady=6)

            ctk.CTkLabel(f, text=sev,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=COLORS["text_muted"]
            ).pack()

            num = ctk.CTkLabel(f, text="0",
                font=ctk.CTkFont("Segoe UI", 20, "bold"),
                text_color=col)
            num.pack()
            self.summary_labels[sev] = num

        # Table header
        table_header = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=8)
        table_header.pack(fill="x", padx=30, pady=(0, 4))

        headers = [("Severity", 100), ("Title", 400),
                   ("Port", 80), ("CVSS", 60)]
        for col_name, width in headers:
            ctk.CTkLabel(table_header, text=col_name, width=width,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=COLORS["text_muted"],
                anchor="w"
            ).pack(side="left", padx=8, pady=8)

        # Scrollable findings list
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True,
                         padx=30, pady=(0, 20))

    def _load_findings(self):
        scan_id = self.scan_entry.get().strip()
        if not scan_id:
            # Load latest scan
            try:
                r = requests.get(
                    "http://localhost:5000/scans", timeout=3)
                scans = r.json()
                if scans:
                    scan_id = str(scans[0]['id'])
                    self.scan_entry.delete(0, 'end')
                    self.scan_entry.insert(0, scan_id)
                else:
                    self.status_label.configure(text="No scans found.")
                    return
            except Exception:
                self.status_label.configure(text="API not reachable.")
                return

        try:
            r = requests.get(
                f"http://localhost:5000/results/{scan_id}",
                timeout=3)

            if r.status_code == 404:
                self.status_label.configure(
                    text=f"Scan #{scan_id} not found.")
                return

            data     = r.json()
            findings = data.get('findings', [])
            summary  = data.get('summary', {})
            scan     = data.get('scan', {})

            # Update summary counts
            for sev, label in self.summary_labels.items():
                label.configure(text=str(summary.get(sev.lower(), 0)))

            self.status_label.configure(
                text=f"Scan #{scan_id} — {scan.get('target','')} "
                     f"— {len(findings)} findings — {scan.get('status','')}")

            # Clear old rows
            for widget in self.scroll.winfo_children():
                widget.destroy()

            if not findings:
                ctk.CTkLabel(self.scroll,
                    text="No findings for this scan.",
                    font=ctk.CTkFont("Segoe UI", 13),
                    text_color=COLORS["text_muted"]
                ).pack(pady=20)
                return

            # Sort by CVSS score descending
            findings.sort(key=lambda x: x.get('cvss_score', 0), reverse=True)

            for f in findings:
                self._add_finding_row(f)

        except requests.exceptions.ConnectionError:
            self.status_label.configure(text="Cannot connect to API.")

    def _add_finding_row(self, finding):
        sev   = finding.get('severity', 'Info')
        color = SEVERITY_COLORS.get(sev, COLORS["text_muted"])

        row = ctk.CTkFrame(self.scroll,
            fg_color=COLORS["bg_card"], corner_radius=8)
        row.pack(fill="x", pady=3)

        # Severity badge
        badge = ctk.CTkFrame(row, fg_color=COLORS["bg_secondary"],
                             corner_radius=6, width=90)
        badge.pack(side="left", padx=8, pady=8)
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=sev,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=color
        ).pack(expand=True)

        # Title
        ctk.CTkLabel(row,
            text=finding.get('title', '')[:60],
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_primary"],
            anchor="w", width=400
        ).pack(side="left", padx=8)

        # Port
        ctk.CTkLabel(row,
            text=finding.get('port', '—'),
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_muted"],
            width=80
        ).pack(side="left")

        # CVSS score
        ctk.CTkLabel(row,
            text=str(finding.get('cvss_score', 0.0)),
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=color,
            width=60
        ).pack(side="left")

        # Expand button
        ctk.CTkButton(row,
            text="Details", width=70, height=28,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_secondary"],
            command=lambda f=finding: self._show_detail(f)
        ).pack(side="right", padx=8)

    def _show_detail(self, finding):
        """Show a popup with full finding details."""
        win = ctk.CTkToplevel(self)
        win.title(finding.get('title', 'Finding Detail'))
        win.geometry("600x400")
        win.configure(fg_color=COLORS["bg_primary"])
        win.grab_set()

        sev   = finding.get('severity', 'Info')
        color = SEVERITY_COLORS.get(sev, COLORS["text_muted"])

        ctk.CTkLabel(win,
            text=finding.get('title', ''),
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color=COLORS["text_primary"],
            wraplength=560
        ).pack(anchor="w", padx=20, pady=(20, 4))

        ctk.CTkLabel(win,
            text=f"Severity: {sev}   |   CVSS: {finding.get('cvss_score',0)}   |   Port: {finding.get('port','—')}",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=color
        ).pack(anchor="w", padx=20, pady=(0, 12))

        for section, key in [("Description", "description"),
                              ("Remediation", "remediation")]:
            ctk.CTkLabel(win, text=section,
                font=ctk.CTkFont("Segoe UI", 13, "bold"),
                text_color=COLORS["text_muted"]
            ).pack(anchor="w", padx=20, pady=(8, 2))

            ctk.CTkLabel(win,
                text=finding.get(key, 'N/A'),
                font=ctk.CTkFont("Segoe UI", 12),
                text_color=COLORS["text_primary"],
                wraplength=560, justify="left"
            ).pack(anchor="w", padx=20)

        ctk.CTkButton(win, text="Close",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=win.destroy
        ).pack(pady=20)