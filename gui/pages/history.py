import customtkinter as ctk
import requests
from gui.theme import COLORS

STATUS_COLORS = {
    'complete': '#97C459',
    'running':  '#FAC775',
    'pending':  '#85B7EB',
    'failed':   '#f09595',
}

class HistoryPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"])
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 16))

        ctk.CTkLabel(header, text="Scan History",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ctk.CTkButton(header, text="⟳  Refresh",
            width=110, height=34,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._load_history
        ).pack(side="right")

        # Table header
        thead = ctk.CTkFrame(self,
            fg_color=COLORS["bg_card"], corner_radius=8)
        thead.pack(fill="x", padx=30, pady=(0, 4))

        for col, width in [("ID", 50), ("Target", 280),
                            ("Status", 100), ("Modules", 260),
                            ("Started", 180)]:
            ctk.CTkLabel(thead, text=col, width=width,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=COLORS["text_muted"], anchor="w"
            ).pack(side="left", padx=8, pady=8)

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True,
                         padx=30, pady=(0, 20))

        self.status_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_muted"]
        )
        self.status_label.pack(pady=4)

    def _load_history(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        try:
            r = requests.get(
                "http://localhost:5000/scans", timeout=3)

            if r.status_code != 200:
                self.status_label.configure(
                    text="Failed to load scans.")
                return

            scans = r.json()

            if not scans:
                ctk.CTkLabel(self.scroll,
                    text="No scans yet. Run a scan first.",
                    font=ctk.CTkFont("Segoe UI", 13),
                    text_color=COLORS["text_muted"]
                ).pack(pady=30)
                self.status_label.configure(text="")
                return

            for scan in scans:
                self._add_scan_row(scan)

            self.status_label.configure(
                text=f"{len(scans)} scan(s) found.")

        except requests.exceptions.ConnectionError:
            self.status_label.configure(
                text="Cannot connect to API.")

    def _add_scan_row(self, scan):
        status = scan.get('status', 'unknown')
        color  = STATUS_COLORS.get(status, COLORS["text_muted"])

        row = ctk.CTkFrame(self.scroll,
            fg_color=COLORS["bg_card"], corner_radius=8)
        row.pack(fill="x", pady=3)

        # ID
        ctk.CTkLabel(row,
            text=f"#{scan.get('id', '?')}",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=COLORS["accent"], width=50, anchor="w"
        ).pack(side="left", padx=8, pady=10)

        # Target
        ctk.CTkLabel(row,
            text=scan.get('target', '—')[:40],
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_primary"],
            width=280, anchor="w"
        ).pack(side="left", padx=4)

        # Status badge
        badge = ctk.CTkFrame(row,
            fg_color=COLORS["bg_secondary"],
            corner_radius=6, width=90)
        badge.pack(side="left", padx=4)
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=status.capitalize(),
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=color
        ).pack(expand=True, pady=4)

        # Modules
        modules = scan.get('modules', [])
        if isinstance(modules, list):
            mod_text = ', '.join(modules)
        else:
            mod_text = str(modules)
        ctk.CTkLabel(row,
            text=mod_text[:35],
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=COLORS["text_muted"],
            width=260, anchor="w"
        ).pack(side="left", padx=4)

        # Started time
        started = scan.get('started_at', '—')
        if started and started != 'None':
            started = started[:19].replace('T', ' ')
        ctk.CTkLabel(row,
            text=started,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=COLORS["text_muted"],
            width=180, anchor="w"
        ).pack(side="left", padx=4)

        # View findings button
        ctk.CTkButton(row,
            text="View Findings",
            width=110, height=28,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_secondary"],
            command=lambda sid=scan.get('id'): self._open_findings(sid)
        ).pack(side="right", padx=8)

    def _open_findings(self, scan_id):
        """Switch to findings page and load this scan."""
        try:
            # Get root app and navigate to findings
            root = self.winfo_toplevel()
            root.show_page("Findings")
            findings_page = root.pages["Findings"]
            findings_page.scan_entry.delete(0, 'end')
            findings_page.scan_entry.insert(0, str(scan_id))
            # small delay to let page render before loading
            self.after(200, findings_page._load_findings)
        except Exception as e:
            print(f"Navigation error: {e}")