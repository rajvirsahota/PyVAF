import customtkinter as ctk
from gui.theme import COLORS

class ScanProgressBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_card"],
                         corner_radius=10)

        self.label = ctk.CTkLabel(
            self, text="Ready to scan",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLORS["text_muted"]
        )
        self.label.pack(anchor="w", padx=16, pady=(12, 4))

        self.bar = ctk.CTkProgressBar(
            self,
            fg_color=COLORS["bg_primary"],
            progress_color=COLORS["accent"],
            height=8,
        )
        self.bar.set(0)
        self.bar.pack(fill="x", padx=16, pady=(0, 4))

        self.pct_label = ctk.CTkLabel(
            self, text="0%",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=COLORS["text_muted"]
        )
        self.pct_label.pack(anchor="e", padx=16, pady=(0, 10))

    def update_progress(self, percent: int, message: str = ""):
        self.bar.set(percent / 100)
        self.pct_label.configure(text=f"{percent}%")
        if message:
            self.label.configure(text=message)

    def reset(self):
        self.bar.set(0)
        self.pct_label.configure(text="0%")
        self.label.configure(text="Ready to scan")