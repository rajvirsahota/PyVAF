import customtkinter as ctk
import requests
from gui.theme import COLORS

class DashboardPage(ctk.CTkFrame):
    def on_show(self):
        self._load_stats()
        
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"])
        self._build_ui()
        

    def _build_ui(self):
        # Title
        ctk.CTkLabel(self,
            text="Dashboard",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=30, pady=(30, 4))

        ctk.CTkLabel(self,
            text="Overview of all scans and findings.",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=30, pady=(0, 24))

        # Stats grid — top row
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=30, pady=(0, 16))

        self.stat_widgets = {}
        stats_config = [
            ("total_scans",    "Total Scans",     COLORS["accent"]),
            ("complete_scans", "Completed",        COLORS["log_ok"]),
            ("total_findings", "Total Findings",   COLORS["log_info"]),
            ("critical",       "Critical",         COLORS["critical"]),
            ("high",           "High",             COLORS["high"]),
            ("medium",         "Medium",           COLORS["medium"]),
        ]

        for key, label, color in stats_config:
            card = ctk.CTkFrame(stats_frame,
                fg_color=COLORS["bg_card"],
                corner_radius=10)
            card.pack(side="left", padx=(0, 10),
                      ipadx=16, ipady=12, fill="y")

            ctk.CTkLabel(card, text=label,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=COLORS["text_muted"]
            ).pack()

            num = ctk.CTkLabel(card, text="—",
                font=ctk.CTkFont("Segoe UI", 28, "bold"),
                text_color=color)
            num.pack()
            self.stat_widgets[key] = num

        # Recent scans section
        ctk.CTkLabel(self,
            text="Recent Scans",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=30, pady=(8, 8))

        # Recent scans list
        self.recent_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=280)
        self.recent_frame.pack(fill="x", padx=30, pady=(0, 16))

        # Refresh button
        
        ctk.CTkButton(self,
            text="⟳  Refresh Dashboard",
            width=180, height=36,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._load_stats
        ).pack(anchor="w", padx=30)

    def _load_stats(self):
        try:
            # Load global stats
            r = requests.get(
                "http://localhost:5000/stats", timeout=3)
            if r.status_code == 200:
                data = r.json()
                for key, widget in self.stat_widgets.items():
                    widget.configure(
                        text=str(data.get(key, 0)))

            # Load recent scans
            r2 = requests.get(
                "http://localhost:5000/scans", timeout=3)
            if r2.status_code == 200:
                scans = r2.json()[:5]  # Last 5 scans
                for w in self.recent_frame.winfo_children():
                    w.destroy()

                if not scans:
                    ctk.CTkLabel(self.recent_frame,
                        text="No scans yet. Go to New Scan to begin.",
                        font=ctk.CTkFont("Segoe UI", 13),
                        text_color=COLORS["text_muted"]
                    ).pack(pady=20)
                    return

                for scan in scans:
                    self._add_recent_row(scan)

        except requests.exceptions.ConnectionError:
            for widget in self.stat_widgets.values():
                widget.configure(text="—")
        except Exception as e:
            print(f"Dashboard load error: {e}")

    def _add_recent_row(self, scan):
        status_colors = {
            'complete': COLORS["log_ok"],
            'running':  COLORS["high"],
            'pending':  COLORS["log_info"],
            'failed':   COLORS["critical"],
        }
        status = scan.get('status', 'unknown')
        color  = status_colors.get(status, COLORS["text_muted"])

        row = ctk.CTkFrame(self.recent_frame,
            fg_color=COLORS["bg_card"], corner_radius=8)
        row.pack(fill="x", pady=3)

        # Scan ID
        ctk.CTkLabel(row,
            text=f"#{scan.get('id','?')}",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=COLORS["accent"], width=40
        ).pack(side="left", padx=12, pady=10)

        # Target
        ctk.CTkLabel(row,
            text=scan.get('target', '—')[:45],
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=4)

        # Status
        ctk.CTkLabel(row,
            text=status.capitalize(),
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=color
        ).pack(side="right", padx=16)

        # Started
        started = scan.get('started_at', '')
        if started:
            started = started[:19].replace('T', ' ')
        ctk.CTkLabel(row,
            text=started,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=COLORS["text_muted"]
        ).pack(side="right", padx=8)