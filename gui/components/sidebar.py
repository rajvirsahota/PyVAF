import customtkinter as ctk
from gui.theme import COLORS, FONTS

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate):
        super().__init__(parent, fg_color=COLORS["bg_secondary"],
                         width=180, corner_radius=0)
        self.on_navigate = on_navigate
        self.buttons = {}
        self.active_page = "Dashboard"

        # App title
        title = ctk.CTkLabel(self, text="PyVAF",
                             font=ctk.CTkFont("Segoe UI", 20, "bold"),
                             text_color=COLORS["accent"])
        title.pack(pady=(20, 4), padx=16, anchor="w")

        subtitle = ctk.CTkLabel(self, text="Vuln Assessment Framework",
                                font=ctk.CTkFont("Segoe UI", 10),
                                text_color=COLORS["text_muted"])
        subtitle.pack(padx=16, anchor="w", pady=(0, 20))

        # Separator
        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=12, pady=(0, 12))

        # Navigation items
        nav_items = [
            ("Dashboard",    "🛡"),
            ("New Scan",     "🔍"),
            ("Findings",     "⚠"),
            ("History",      "📋"),
            ("Reports",      "📄"),
        ]

        for name, icon in nav_items:
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {name}",
                anchor="w",
                height=40,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_card"],
                font=ctk.CTkFont("Segoe UI", 13),
                command=lambda n=name: self.navigate(n)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.buttons[name] = btn

        # Settings at bottom
        self.pack_propagate(False)
        settings_btn = ctk.CTkButton(
            self, text="  ⚙   Settings", anchor="w",
            height=40, fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_card"],
            font=ctk.CTkFont("Segoe UI", 13)
        )
        settings_btn.pack(side="bottom", fill="x", padx=8, pady=12)

        self.navigate("Dashboard")

    def navigate(self, page_name):
        # Reset previous active button
        if self.active_page in self.buttons:
            self.buttons[self.active_page].configure(
                fg_color="transparent",
                text_color=COLORS["text_muted"]
            )
        # Highlight new active button
        self.active_page = page_name
        if page_name in self.buttons:
            self.buttons[page_name].configure(
                fg_color=COLORS["bg_card"],
                text_color=COLORS["accent"]
            )
        self.on_navigate(page_name)