"""
Modern UI Styles for APK Finder Client
"""

# Light Theme Colors
LIGHT_COLORS = {
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

# Dark Theme Colors
DARK_COLORS = {
    "primary": "#3B82F6",      # Blue
    "primary_hover": "#2563EB",
    "secondary": "#8B5CF6",    # Purple
    "secondary_hover": "#7C3AED",
    "background": "#1E293B",
    "surface": "#334155",
    "surface_hover": "#475569",
    "border": "#475569",
    "text_primary": "#F1F5F9",
    "text_secondary": "#CBD5E1",
    "text_muted": "#94A3B8",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "white": "#FFFFFF"
}

# Default to light theme
COLORS = LIGHT_COLORS.copy()

def get_theme_colors(theme: str = "Light"):
    """Get color palette for the specified theme"""
    if theme.lower() == "dark":
        return DARK_COLORS
    else:
        return LIGHT_COLORS

def update_colors(theme: str = "Light"):
    """Update global COLORS dictionary with theme colors"""
    global COLORS
    COLORS.clear()
    COLORS.update(get_theme_colors(theme))


def get_complete_style(theme: str = "Light"):
    """Get complete stylesheet for the specified theme"""
    colors = get_theme_colors(theme)
    
    # Main Application Style
    main_style = f"""
    QMainWindow {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
        font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
        font-size: 14px;
    }}
    
    /* Central widget - force background color */
    QWidget#centralWidget {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
    }}
    
    /* Default QWidget styling */
    QWidget {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
    }}
    
    /* Make sure specific widgets use appropriate backgrounds */
    QTabWidget QWidget {{
        background-color: transparent;
    }}
    
    QGroupBox QWidget {{
        background-color: transparent;
    }}
    
    QScrollArea {{
        background-color: {colors["background"]};
        border: none;
    }}
    
    QScrollArea > QWidget > QWidget {{
        background-color: {colors["background"]};
    }}
    
    QSplitter {{
        background-color: {colors["background"]};
    }}
    
    QSplitter::handle {{
        background-color: {colors["border"]};
    }}
    
    QFrame {{
        background-color: {colors["background"]};
    }}
    """
    
    # Tab Widget Style
    tab_style = f"""
    QTabWidget::pane {{
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        background-color: {colors["surface"]};
        margin-top: 5px;
    }}
    
    QTabWidget::tab-bar {{
        alignment: left;
    }}
    
    QTabBar::tab {{
        background-color: {colors["background"]};
        color: {colors["text_secondary"]};
        border: 1px solid {colors["border"]};
        border-bottom: none;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 500;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
        border-color: {colors["primary"]};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {colors["surface_hover"]};
        color: {colors["text_primary"]};
    }}
    """
    
    # Button Styles
    button_style = f"""
    QPushButton {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["primary_hover"]};
    }}
    
    QPushButton:pressed {{
        background-color: {colors["primary_hover"]};
        border: 1px solid {colors["primary_hover"]};
    }}
    
    QPushButton:disabled {{
        background-color: {colors["text_muted"]};
        color: {colors["white"]};
    }}
    
    QPushButton#primaryButton {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
    }}
    
    QPushButton#primaryButton:hover {{
        background-color: {colors["primary_hover"]};
    }}
    
    QPushButton#secondaryButton {{
        background-color: {colors["secondary"]};
        color: {colors["white"]};
    }}
    
    QPushButton#secondaryButton:hover {{
        background-color: {colors["secondary_hover"]};
    }}
    
    QPushButton#outlineButton {{
        background-color: {colors["surface"]};
        color: {colors["primary"]};
        border: 2px solid {colors["primary"]};
    }}
    
    QPushButton#outlineButton:hover {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
    }}
    
    QPushButton#serverButton {{
        background-color: {colors["surface"]};
        color: {colors["text_primary"]};
        border: 2px solid {colors["border"]};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
        min-width: 100px;
    }}
    
    QPushButton#serverButton:hover {{
        background-color: {colors["surface_hover"]};
        border-color: {colors["primary"]};
    }}
    
    QPushButton#serverButton:checked {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
        border-color: {colors["primary"]};
    }}
    
    QPushButton#serverButton:checked:hover {{
        background-color: {colors["primary_hover"]};
        border-color: {colors["primary_hover"]};
    }}
    
    QPushButton#buildTypeButton {{
        background-color: {colors["surface"]};
        color: {colors["text_primary"]};
        border: 2px solid {colors["border"]};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
        min-width: 80px;
    }}
    
    QPushButton#buildTypeButton:hover {{
        background-color: {colors["surface_hover"]};
        border-color: {colors["secondary"]};
    }}
    
    QPushButton#buildTypeButton:checked {{
        background-color: {colors["secondary"]};
        color: {colors["white"]};
        border-color: {colors["secondary"]};
    }}
    
    QPushButton#buildTypeButton:checked:hover {{
        background-color: {colors["secondary_hover"]};
        border-color: {colors["secondary_hover"]};
    }}
    """
    
    # Search Input Style
    search_input_style = f"""
    QLineEdit {{
        background-color: {colors["background"]};
        border: 2px solid {colors["border"]};
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 14px;
        color: {colors["text_primary"]};
    }}
    
    QLineEdit:focus {{
        border-color: {colors["primary"]};
        outline: none;
    }}
    
    QLineEdit::placeholder {{
        color: {colors["text_muted"]};
    }}
    """
    
    # Table Widget Style
    table_style = f"""
    QTableWidget {{
        background-color: {colors["background"]};
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        gridline-color: {colors["border"]};
        selection-background-color: {colors["primary"]};
        selection-color: {colors["white"]};
        font-size: 13px;
    }}
    
    QTableWidget::item {{
        padding: 12px 8px;
        border-bottom: 1px solid {colors["border"]};
    }}
    
    QTableWidget::item:selected {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
    }}
    
    QTableWidget::item:hover {{
        background-color: {colors["surface_hover"]};
    }}
    
    QHeaderView::section {{
        background-color: {colors["surface"]};
        color: {colors["text_primary"]};
        padding: 12px 8px;
        border: none;
        border-bottom: 2px solid {colors["border"]};
        font-weight: 600;
    }}
    
    QHeaderView::section:hover {{
        background-color: {colors["surface_hover"]};
    }}
    """
    
    # Scroll Bar Style
    scrollbar_style = f"""
    QScrollBar:vertical {{
        background-color: {colors["surface"]};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors["text_muted"]};
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors["text_secondary"]};
    }}
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {colors["surface"]};
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors["text_muted"]};
        border-radius: 6px;
        min-width: 20px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {colors["text_secondary"]};
    }}
    
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    """
    
    # Status Bar Style
    status_bar_style = f"""
    QStatusBar {{
        background-color: {colors["surface"]};
        border-top: 1px solid {colors["border"]};
        color: {colors["text_secondary"]};
        font-size: 12px;
        padding: 5px;
    }}
    """
    
    # Label Styles
    label_style = f"""
    QLabel {{
        color: {colors["text_primary"]};
        font-size: 14px;
    }}
    """
    
    # Progress Bar Style
    progress_bar_style = f"""
    QProgressBar {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 6px;
        text-align: center;
        font-weight: 500;
        color: {colors["text_primary"]};
    }}
    
    QProgressBar::chunk {{
        background-color: {colors["primary"]};
        border-radius: 5px;
    }}
    """
    
    # ComboBox Style
    combobox_style = f"""
    QComboBox {{
        background-color: {colors["background"]};
        border: 2px solid {colors["border"]};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
        color: {colors["text_primary"]};
        min-width: 120px;
    }}
    
    QComboBox:focus {{
        border-color: {colors["primary"]};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {colors["text_secondary"]};
        margin-right: 5px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {colors["background"]};
        border: 1px solid {colors["border"]};
        border-radius: 6px;
        selection-background-color: {colors["primary"]};
        selection-color: {colors["white"]};
        outline: none;
    }}
    """
    
    # Menu Style
    menu_style = f"""
    QMenu {{
        background-color: {colors["background"]};
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        padding: 5px;
        color: {colors["text_primary"]};
    }}
    
    QMenu::item {{
        background-color: transparent;
        padding: 8px 16px;
        border-radius: 4px;
        margin: 1px;
    }}
    
    QMenu::item:selected {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
    }}
    
    QMenu::item:disabled {{
        color: {colors["text_muted"]};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {colors["border"]};
        margin: 5px;
    }}
    """
    
    # Group Box Style
    groupbox_style = f"""
    QGroupBox {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 10px;
        font-weight: 600;
        color: {colors["text_primary"]};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        background-color: {colors["surface"]};
        margin-left: 10px;
    }}
    
    QTextEdit {{
        background-color: {colors["background"]};
        border: 1px solid {colors["border"]};
        border-radius: 6px;
        padding: 8px;
        color: {colors["text_primary"]};
        font-size: 13px;
    }}
    
    QTextEdit:focus {{
        border-color: {colors["primary"]};
    }}
    
    QCheckBox {{
        color: {colors["text_primary"]};
        font-size: 14px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {colors["border"]};
        border-radius: 3px;
        background-color: {colors["background"]};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {colors["primary"]};
        border-color: {colors["primary"]};
    }}
    
    QSpinBox {{
        background-color: {colors["background"]};
        border: 2px solid {colors["border"]};
        border-radius: 6px;
        padding: 6px 8px;
        font-size: 14px;
        color: {colors["text_primary"]};
    }}
    
    QSpinBox:focus {{
        border-color: {colors["primary"]};
    }}
    """
    
    return f"""
    {main_style}
    {tab_style}
    {button_style}
    {search_input_style}
    {table_style}
    {scrollbar_style}
    {status_bar_style}
    {label_style}
    {progress_bar_style}
    {combobox_style}
    {menu_style}
    {groupbox_style}
    """

# Generate style constants for backward compatibility
def _generate_style_constants(theme: str = "Light"):
    """Generate style constants for the given theme"""
    colors = get_theme_colors(theme)
    
    # Button Styles
    button_style = f"""
    QPushButton {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["primary_hover"]};
    }}
    
    QPushButton:pressed {{
        background-color: {colors["primary_hover"]};
        border: 1px solid {colors["primary_hover"]};
    }}
    
    QPushButton:disabled {{
        background-color: {colors["text_muted"]};
        color: {colors["white"]};
    }}
    """
    
    secondary_button_style = f"""
    QPushButton {{
        background-color: {colors["secondary"]};
        color: {colors["white"]};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["secondary_hover"]};
    }}
    
    QPushButton:pressed {{
        background-color: {colors["secondary_hover"]};
    }}
    """
    
    outline_button_style = f"""
    QPushButton {{
        background-color: transparent;
        color: {colors["primary"]};
        border: 2px solid {colors["primary"]};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 500;
        font-size: 14px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
    }}
    
    QPushButton:pressed {{
        background-color: {colors["primary_hover"]};
        color: {colors["white"]};
    }}
    """
    
    server_button_style = f"""
    QPushButton {{
        background-color: {colors["surface"]};
        color: {colors["text_primary"]};
        border: 2px solid {colors["border"]};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
        min-width: 100px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["surface_hover"]};
        border-color: {colors["primary"]};
    }}
    
    QPushButton:checked {{
        background-color: {colors["primary"]};
        color: {colors["white"]};
        border-color: {colors["primary"]};
    }}
    """
    
    return button_style, secondary_button_style, outline_button_style, server_button_style

# Initialize backward compatibility constants
BUTTON_STYLE, SECONDARY_BUTTON_STYLE, OUTLINE_BUTTON_STYLE, SERVER_BUTTON_STYLE = _generate_style_constants("Light")
COMPLETE_STYLE = get_complete_style("Light")

def update_style_constants(theme: str = "Light"):
    """Update style constants when theme changes"""
    global BUTTON_STYLE, SECONDARY_BUTTON_STYLE, OUTLINE_BUTTON_STYLE, SERVER_BUTTON_STYLE, COMPLETE_STYLE
    BUTTON_STYLE, SECONDARY_BUTTON_STYLE, OUTLINE_BUTTON_STYLE, SERVER_BUTTON_STYLE = _generate_style_constants(theme)
    COMPLETE_STYLE = get_complete_style(theme)