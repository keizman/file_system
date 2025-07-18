"""
Modern UI Styles for APK Finder Client
"""

# Color Palette
COLORS = {
    "primary": "#3B82F6",      # Blue
    "primary_hover": "#2563EB",
    "secondary": "#8B5CF6",    # Purple
    "secondary_hover": "#7C3AED",
    "background": "#FFFFFF",
    "surface": "#F8FAFC",
    "surface_hover": "#F1F5F9",
    "border": "#E2E8F0",
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "white": "#FFFFFF"
}

# Main Application Style
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {COLORS["background"]};
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
    font-size: 14px;
}}

QWidget {{
    background-color: transparent;
    color: {COLORS["text_primary"]};
}}
"""

# Tab Widget Style
TAB_STYLE = f"""
QTabWidget::pane {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    background-color: {COLORS["surface"]};
    margin-top: 5px;
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background-color: {COLORS["background"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS["primary"]};
    color: {COLORS["white"]};
    border-color: {COLORS["primary"]};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS["surface_hover"]};
    color: {COLORS["text_primary"]};
}}
"""

# Button Styles
BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS["primary"]};
    color: {COLORS["white"]};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 14px;
}}

QPushButton:hover {{
    background-color: {COLORS["primary_hover"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["primary_hover"]};
    transform: translateY(1px);
}}

QPushButton:disabled {{
    background-color: {COLORS["text_muted"]};
    color: {COLORS["white"]};
}}
"""

SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS["secondary"]};
    color: {COLORS["white"]};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 14px;
}}

QPushButton:hover {{
    background-color: {COLORS["secondary_hover"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["secondary_hover"]};
}}
"""

OUTLINE_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS["primary"]};
    border: 2px solid {COLORS["primary"]};
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 14px;
}}

QPushButton:hover {{
    background-color: {COLORS["primary"]};
    color: {COLORS["white"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["primary_hover"]};
    color: {COLORS["white"]};
}}
"""

# Search Input Style
SEARCH_INPUT_STYLE = f"""
QLineEdit {{
    background-color: {COLORS["background"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    color: {COLORS["text_primary"]};
}}

QLineEdit:focus {{
    border-color: {COLORS["primary"]};
    outline: none;
}}

QLineEdit::placeholder {{
    color: {COLORS["text_muted"]};
}}
"""

# Table Widget Style
TABLE_STYLE = f"""
QTableWidget {{
    background-color: {COLORS["background"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    gridline-color: {COLORS["border"]};
    selection-background-color: {COLORS["primary"]};
    selection-color: {COLORS["white"]};
    font-size: 13px;
}}

QTableWidget::item {{
    padding: 12px 8px;
    border-bottom: 1px solid {COLORS["border"]};
}}

QTableWidget::item:selected {{
    background-color: {COLORS["primary"]};
    color: {COLORS["white"]};
}}

QTableWidget::item:hover {{
    background-color: {COLORS["surface_hover"]};
}}

QHeaderView::section {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text_primary"]};
    padding: 12px 8px;
    border: none;
    border-bottom: 2px solid {COLORS["border"]};
    font-weight: 600;
}}

QHeaderView::section:hover {{
    background-color: {COLORS["surface_hover"]};
}}
"""

# Scroll Bar Style
SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background-color: {COLORS["surface"]};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["text_muted"]};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["text_secondary"]};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS["surface"]};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS["text_muted"]};
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS["text_secondary"]};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""

# Status Bar Style
STATUS_BAR_STYLE = f"""
QStatusBar {{
    background-color: {COLORS["surface"]};
    border-top: 1px solid {COLORS["border"]};
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    padding: 5px;
}}
"""

# Label Styles
LABEL_STYLE = f"""
QLabel {{
    color: {COLORS["text_primary"]};
    font-size: 14px;
}}
"""

TITLE_LABEL_STYLE = f"""
QLabel {{
    color: {COLORS["text_primary"]};
    font-size: 18px;
    font-weight: bold;
    margin: 10px 0;
}}
"""

SUBTITLE_LABEL_STYLE = f"""
QLabel {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    margin: 5px 0;
}}
"""

# Progress Bar Style
PROGRESS_BAR_STYLE = f"""
QProgressBar {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    text-align: center;
    font-weight: 500;
    color: {COLORS["text_primary"]};
}}

QProgressBar::chunk {{
    background-color: {COLORS["primary"]};
    border-radius: 5px;
}}
"""

# ComboBox Style
COMBOBOX_STYLE = f"""
QComboBox {{
    background-color: {COLORS["background"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: {COLORS["text_primary"]};
    min-width: 120px;
}}

QComboBox:focus {{
    border-color: {COLORS["primary"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS["text_secondary"]};
    margin-right: 5px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["background"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    selection-background-color: {COLORS["primary"]};
    selection-color: {COLORS["white"]};
    outline: none;
}}
"""

# Menu Style
MENU_STYLE = f"""
QMenu {{
    background-color: {COLORS["background"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 5px;
    color: {COLORS["text_primary"]};
}}

QMenu::item {{
    background-color: transparent;
    padding: 8px 16px;
    border-radius: 4px;
    margin: 1px;
}}

QMenu::item:selected {{
    background-color: {COLORS["primary"]};
    color: {COLORS["white"]};
}}

QMenu::item:disabled {{
    color: {COLORS["text_muted"]};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS["border"]};
    margin: 5px;
}}
"""

# Group Box Style
GROUPBOX_STYLE = f"""
QGroupBox {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: 600;
    color: {COLORS["text_primary"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: {COLORS["surface"]};
    margin-left: 10px;
}}
"""

# Complete style sheet
COMPLETE_STYLE = f"""
{MAIN_STYLE}
{TAB_STYLE}
{BUTTON_STYLE}
{SEARCH_INPUT_STYLE}
{TABLE_STYLE}
{SCROLLBAR_STYLE}
{STATUS_BAR_STYLE}
{LABEL_STYLE}
{PROGRESS_BAR_STYLE}
{COMBOBOX_STYLE}
{MENU_STYLE}
{GROUPBOX_STYLE}
"""