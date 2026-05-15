import customtkinter as ctk
import requests
from gui.theme import COLORS
from gui.components.log_viewer import LogViewer
from gui.components.progress_bar import ScanProgressBar
from core.scanner import log_queue

class NewScanPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"])
        self.current_scan_id = None
        self._build_ui()
        self._poll_log()

    def _build_ui(self):
        ctk.CTkLabel(self, text="New Scan",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=30, pady=(30, 4))

        ctk.CTkLabel(self,
            text="Enter a target IP, domain, or URL to begin.",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=30, pady=(0, 16))

        # Input card
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                            corner_radius=12)
        card.pack(fill="x", padx=30, pady=(0, 12))

        ctk.CTkLabel(card, text="Target",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(16, 4))

        self.target_entry = ctk.CTkEntry(
            card,
            placeholder_text="e.g. 192.168.1.1 or scanme.nmap.org",
            height=40,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=COLORS["bg_primary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"]
        )
        self.target_entry.pack(fill="x", padx=20, pady=(0, 12))

        # Modules
        ctk.CTkLabel(card, text="Scan Modules",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(0, 6))

        mframe = ctk.CTkFrame(card, fg_color="transparent")
        mframe.pack(fill="x", padx=20, pady=(0, 12))

        self.module_vars = {}
        modules = [
    ("port", "Port Scanner"),
    ("web",  "Web Scanner"),
    ("ssl",  "SSL/TLS Check"),
    ("dns",  "DNS Recon"),
    ("cve",  "CVE Lookup"),
]

        for i, (key, label) in enumerate(modules):
            var = ctk.BooleanVar(value=True)
            self.module_vars[key] = var
            ctk.CTkCheckBox(mframe, text=label, variable=var,
                font=ctk.CTkFont("Segoe UI", 13),
                text_color=COLORS["text_primary"],
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"]
            ).grid(row=i//2, column=i%2, sticky="w", padx=12, pady=4)

        self.scan_btn = ctk.CTkButton(card,
            text="▶  Start Scan", height=44,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._start_scan
        )
        self.scan_btn.pack(fill="x", padx=20, pady=(0, 20))

        # Progress bar
        self.progress = ScanProgressBar(self)
        self.progress.pack(fill="x", padx=30, pady=(0, 12))

        # Live log viewer
        self.log_viewer = LogViewer(self)
        self.log_viewer.pack(fill="both", expand=True, padx=30, pady=(0, 20))

    def _start_scan(self):
        target   = self.target_entry.get().strip()
        selected = [k for k, v in self.module_vars.items() if v.get()]
        
        # Validate target
        if not target:
            self.log_viewer.append("[WARN]", "Please enter a target.")
            return
        
        forbidden = [' ', '&&', ';', '|', '`']
        for char in forbidden:
            if char in target:
                self.log_viewer.append("[WARN]",f"Invalid character in target: '{char}'")
                return

        if not selected:
            self.log_viewer.append("[WARN]", "Select at least one module.")
            return

        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.log_viewer.clear()
        self.progress.reset()
        self.progress.update_progress(0, "Starting scan...")

        try:
            response = requests.post(
                "http://localhost:5000/scan",
                json={"target": target, "modules": selected},
                timeout=3
            )
            if response.status_code == 201:
                data = response.json()
                self.current_scan_id = data['scan']['id']
                self.log_viewer.append("[INFO]",
                    f"Scan #{self.current_scan_id} started on '{target}'")
                self.log_viewer.append("[INFO]",f"Modules: {', '.join(selected)}")
            else:
                self.log_viewer.append("[ERR]", f"API error: {response.text}")
                self.scan_btn.configure(state="normal", text="▶  Start Scan")

        except requests.exceptions.ConnectionError:
            self.log_viewer.append("[ERR]", "Cannot connect to API.")
            self.scan_btn.configure(state="normal", text="▶  Start Scan")
        except requests.exceptions.Timeout:
            self.log_viewer.append("[ERR]","API request timed out.")
            self.scan_btn.configure(state="normal", text="▶  Start Scan")    

    def _poll_log(self):
        """Poll the log queue every 200ms -- only activate during scan."""
        if self.current_scan_id is not None:
            try:
                while not log_queue.empty():
                    level, message = log_queue.get_nowait()

                    if level == "[PROGRESS]":
                        pct = int(message)
                        self.progress.update_progress(pct, f"Running modules... {pct}%")

                    elif level == "[DONE]":
                         
                         self.progress.update_progress(100, "Scan complete!")
                         self.scan_btn.configure(
                        state="normal", text="▶  Start Scan")
                         self.log_viewer.append("[OK]",
                        "All modules finished. Check Findings page.")
                         self.current_scan_id = None #Stop polling

                    else:
                         
                         self.log_viewer.append(level, message)

            except Exception:

                pass
            

        # Always reschedule but queue only read during active scan
        self.after(200, self._poll_log)