import customtkinter as ctk

def apply_theme():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

COLORS = {
    "bg_primary":    "#1a1b26",
    "bg_secondary":  "#13141f",
    "bg_card":       "#252638",
    "accent":        "#7c3aed",
    "accent_hover":  "#6d28d9",
    "border":        "#2a2b3d",
    "text_primary":  "#c9ccd6",
    "text_muted":    "#6b6d80",
    "critical":      "#f09595",
    "high":          "#FAC775",
    "medium":        "#97C459",
    "low":           "#85B7EB",
    "info":          "#8b8d9e",
    "log_ok":        "#5DCAA5",
    "log_warn":      "#FAC775",
    "log_err":       "#f09595",
    "log_info":      "#85B7EB",
}

FONTS = {
    "title":   ("Segoe UI", 18, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "body":    ("Segoe UI", 13),
    "small":   ("Segoe UI", 11),
    "mono":    ("Courier New", 11),
}