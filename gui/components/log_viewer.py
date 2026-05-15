import customtkinter as ctk
from gui.theme import COLORS

class LogViewer(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_secondary"],
                         corner_radius=10)

        ctk.CTkLabel(self, text="Live Log",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont("Courier New", 11),
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            state="disabled",
            wrap="word",
            height=160,
        )
        self.text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Color tags mapped to log levels
        self.colors = {
            "[OK]":       COLORS["log_ok"],
            "[INFO]":     COLORS["log_info"],
            "[WARN]":     COLORS["log_warn"],
            "[ERR]":      COLORS["critical"],
            "[PROGRESS]": COLORS["accent"],
            "[DONE]":     COLORS["log_ok"],
        }

    def append(self, level: str, message: str):
        color = self.colors.get(level, COLORS["text_muted"])
        line  = f"{level:<12} {message}\n"

        self.text.configure(state="normal")
        self.text.insert("end", line)
        self.text.configure(state="disabled")
        self.text.see("end")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")