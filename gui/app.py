import customtkinter as ctk
import tkinter as tk
from gui.theme import apply_theme, COLORS
from gui.components.sidebar import Sidebar
from gui.pages.dashboard import DashboardPage
from gui.pages.new_scan import NewScanPage
from gui.pages.findings import FindingsPage
from gui.pages.history import HistoryPage
from gui.pages.reports import ReportsPage

class VAFApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_theme()

        self.title("PyVAF — Vulnerability Assessment Framework")
        self.geometry("1200x720")
        self.minsize(1000, 640)
        self.configure(fg_color=COLORS["bg_primary"])

        # Global exception handler
        self.report_callback_exception = self._handle_exception

        self.pages = {}
        self._build_layout()

    def _handle_exception(self, exc, val, tb):
        import traceback
        print(f"[ERROR] Unhandled GUI exception: {val}")
        traceback.print_tb(tb)

    def _build_layout(self):
        # Content area first
        self.content = ctk.CTkFrame(
            self, fg_color=COLORS["bg_primary"])
        self.content.pack(side="left", fill="both", expand=True)

        # Instantiate all pages
        self.pages = {
            "Dashboard": DashboardPage(self.content),
            "New Scan":  NewScanPage(self.content),
            "Findings":  FindingsPage(self.content),
            "History":   HistoryPage(self.content),
            "Reports":   ReportsPage(self.content),
        }

        for page in self.pages.values():
            page.place(relx=0, rely=0,
                       relwidth=1, relheight=1)

        # Sidebar after pages
        self.sidebar = Sidebar(self, on_navigate=self.show_page)
        self.sidebar.pack(side="left", fill="y")

        border = ctk.CTkFrame(
            self, width=1, fg_color=COLORS["border"])
        border.pack(side="left", fill="y")

        self.show_page("Dashboard")

    def show_page(self, name):
        if hasattr(self, 'pages') and name in self.pages:
            self.pages[name].lift()
            if name == "Dashboard":
                self.pages["Dashboard"].on_show()
            if name == "History":
                self.pages["History"]._load_history()
            if name == "Reports":
                self.pages["Reports"]._load_report_list()