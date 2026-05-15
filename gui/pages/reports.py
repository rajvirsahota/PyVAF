import customtkinter as ctk
import requests
import os
import subprocess
import platform
from gui.theme import COLORS

class ReportsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"])
        self._build_ui()

    def _build_ui(self):
        # Header
        ctk.CTkLabel(self,
            text="Reports",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=30, pady=(30, 4))

        ctk.CTkLabel(self,
            text="Generate and download PDF pentest reports.",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=30, pady=(0, 20))

        # Generate card
        gen_card = ctk.CTkFrame(self,
            fg_color=COLORS["bg_card"], corner_radius=12)
        gen_card.pack(fill="x", padx=30, pady=(0, 16))

        ctk.CTkLabel(gen_card,
            text="Generate New Report",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(16, 8))

        # Scan ID row
        row = ctk.CTkFrame(gen_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(row, text="Scan ID:",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(0, 8))

        self.scan_id_entry = ctk.CTkEntry(
            row, width=100, height=36,
            placeholder_text="e.g. 1",
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=COLORS["bg_primary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"]
        )
        self.scan_id_entry.pack(side="left", padx=(0, 12))

        self.gen_btn = ctk.CTkButton(
            row,
            text="📄  Generate PDF",
            height=36,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._generate_report
        )
        self.gen_btn.pack(side="left")

        self.gen_status = ctk.CTkLabel(
            gen_card, text="",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["log_ok"]
        )
        self.gen_status.pack(anchor="w", padx=20, pady=(0, 16))

        # Existing reports section
        reports_header = ctk.CTkFrame(
            self, fg_color="transparent")
        reports_header.pack(fill="x", padx=30, pady=(0, 8))

        ctk.CTkLabel(reports_header,
            text="Generated Reports",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ctk.CTkButton(reports_header,
            text="⟳  Refresh",
            width=100, height=32,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._load_reports
        ).pack(side="right")

        # Reports list
        self.reports_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent")
        self.reports_scroll.pack(
            fill="both", expand=True, padx=30, pady=(0, 20))

        self._load_reports()

    def _generate_report(self):
        scan_id = self.scan_id_entry.get().strip()

        if not scan_id:
            self.gen_status.configure(
                text="⚠  Enter a scan ID.",
                text_color=COLORS["high"])
            return

        self.gen_btn.configure(
            state="disabled", text="Generating...")
        self.gen_status.configure(
            text="⏳  Generating report...",
            text_color=COLORS["text_muted"])

        try:
            r = requests.post(
                f"http://localhost:5000/report/{scan_id}",
                timeout=30)

            if r.status_code == 200:
                data     = r.json()
                filename = data.get('file', '')
                self.gen_status.configure(
                    text=f"✅  Saved: {filename}",
                    text_color=COLORS["log_ok"])
                self._load_reports()
            else:
                err = r.json().get('error', 'Unknown error')
                self.gen_status.configure(
                    text=f"❌  Error: {err}",
                    text_color=COLORS["critical"])

        except requests.exceptions.ConnectionError:
            self.gen_status.configure(
                text="❌  Cannot connect to API.",
                text_color=COLORS["critical"])
        except Exception as e:
            self.gen_status.configure(
                text=f"❌  {str(e)}",
                text_color=COLORS["critical"])
        finally:
            self.gen_btn.configure(
                state="normal", text="📄  Generate PDF")

    def _load_reports(self):
        for w in self.reports_scroll.winfo_children():
            w.destroy()

        try:
            r = requests.get(
                "http://localhost:5000/reports", timeout=5)

            if r.status_code != 200:
                return

            files = r.json()

            if not files:
                ctk.CTkLabel(self.reports_scroll,
                    text="No reports yet. Generate one above.",
                    font=ctk.CTkFont("Segoe UI", 13),
                    text_color=COLORS["text_muted"]
                ).pack(pady=20)
                return

            for f in files:
                self._add_report_row(f)

        except Exception:
            pass

    def _add_report_row(self, file_info):
        row = ctk.CTkFrame(self.reports_scroll,
            fg_color=COLORS["bg_card"], corner_radius=8)
        row.pack(fill="x", pady=3)

        # PDF icon + filename
        ctk.CTkLabel(row,
            text="📄",
            font=ctk.CTkFont("Segoe UI", 18)
        ).pack(side="left", padx=12, pady=10)

        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info_frame,
            text=file_info.get('filename', ''),
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w")

        size_kb = round(file_info.get('size', 0) / 1024, 1)
        ctk.CTkLabel(info_frame,
            text=f"{size_kb} KB",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=COLORS["text_muted"],
            anchor="w"
        ).pack(anchor="w")

        # Open button
        ctk.CTkButton(row,
            text="Open PDF",
            width=90, height=30,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=lambda p=file_info.get('path',''): self._open_pdf(p)
        ).pack(side="right", padx=8)

    def _open_pdf(self, path):
        """Open PDF with system default viewer."""
        try:
            abs_path = os.path.abspath(path)
            if platform.system() == 'Windows':
                os.startfile(abs_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', abs_path])
            else:
                subprocess.run(['xdg-open', abs_path])
        except Exception as e:
            print(f"Could not open PDF: {e}")