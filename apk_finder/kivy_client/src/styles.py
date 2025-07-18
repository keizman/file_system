"""
Kivy UI Styles for APK Finder Client
"""

from kivy.utils import get_color_from_hex


# Light Theme Colors
LIGHT_COLORS = {
    "primary": get_color_from_hex("#3B82F6"),      # Blue
    "primary_hover": get_color_from_hex("#2563EB"),
    "secondary": get_color_from_hex("#8B5CF6"),    # Purple
    "secondary_hover": get_color_from_hex("#7C3AED"),
    "background": get_color_from_hex("#FFFFFF"),
    "surface": get_color_from_hex("#F8FAFC"),
    "surface_hover": get_color_from_hex("#F1F5F9"),
    "border": get_color_from_hex("#E2E8F0"),
    "text_primary": get_color_from_hex("#1E293B"),
    "text_secondary": get_color_from_hex("#64748B"),
    "text_muted": get_color_from_hex("#94A3B8"),
    "success": get_color_from_hex("#10B981"),
    "warning": get_color_from_hex("#F59E0B"),
    "error": get_color_from_hex("#EF4444"),
    "white": get_color_from_hex("#FFFFFF"),
    "transparent": [0, 0, 0, 0]
}

# Dark Theme Colors
DARK_COLORS = {
    "primary": get_color_from_hex("#3B82F6"),      # Blue
    "primary_hover": get_color_from_hex("#2563EB"),
    "secondary": get_color_from_hex("#8B5CF6"),    # Purple
    "secondary_hover": get_color_from_hex("#7C3AED"),
    "background": get_color_from_hex("#1E293B"),
    "surface": get_color_from_hex("#334155"),
    "surface_hover": get_color_from_hex("#475569"),
    "border": get_color_from_hex("#475569"),
    "text_primary": get_color_from_hex("#F1F5F9"),
    "text_secondary": get_color_from_hex("#CBD5E1"),
    "text_muted": get_color_from_hex("#94A3B8"),
    "success": get_color_from_hex("#10B981"),
    "warning": get_color_from_hex("#F59E0B"),
    "error": get_color_from_hex("#EF4444"),
    "white": get_color_from_hex("#FFFFFF"),
    "transparent": [0, 0, 0, 0]
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


def apply_button_style(button, style_type="primary"):
    """Apply style to a button"""
    if style_type == "primary":
        button.background_color = COLORS["primary"]
        button.color = COLORS["white"]
    elif style_type == "secondary":
        button.background_color = COLORS["secondary"]
        button.color = COLORS["white"]
    elif style_type == "outline":
        button.background_color = COLORS["transparent"]
        button.color = COLORS["primary"]
    elif style_type == "success":
        button.background_color = COLORS["success"]
        button.color = COLORS["white"]
    elif style_type == "error":
        button.background_color = COLORS["error"]
        button.color = COLORS["white"]
    elif style_type == "warning":
        button.background_color = COLORS["warning"]
        button.color = COLORS["white"]


def apply_input_style(input_widget):
    """Apply style to an input widget"""
    input_widget.background_color = COLORS["background"]
    input_widget.foreground_color = COLORS["text_primary"]
    input_widget.cursor_color = COLORS["primary"]


def apply_label_style(label, style_type="primary"):
    """Apply style to a label"""
    if style_type == "primary":
        label.color = COLORS["text_primary"]
    elif style_type == "secondary":
        label.color = COLORS["text_secondary"]
    elif style_type == "muted":
        label.color = COLORS["text_muted"]
    elif style_type == "success":
        label.color = COLORS["success"]
    elif style_type == "error":
        label.color = COLORS["error"]
    elif style_type == "warning":
        label.color = COLORS["warning"]


def get_surface_color():
    """Get surface color for containers"""
    return COLORS["surface"]


def get_background_color():
    """Get background color"""
    return COLORS["background"]


def get_border_color():
    """Get border color"""
    return COLORS["border"]


def get_text_color():
    """Get primary text color"""
    return COLORS["text_primary"]


# Kivy KV string for common styles
KV_STYLES = '''
<StyledButton@Button>:
    background_color: app.colors["primary"] if hasattr(app, 'colors') else [0.23, 0.51, 0.96, 1]
    color: app.colors["white"] if hasattr(app, 'colors') else [1, 1, 1, 1]
    font_size: dp(14)
    size_hint_y: None
    height: dp(40)

<StyledSecondaryButton@Button>:
    background_color: app.colors["secondary"] if hasattr(app, 'colors') else [0.55, 0.36, 0.96, 1]
    color: app.colors["white"] if hasattr(app, 'colors') else [1, 1, 1, 1]
    font_size: dp(14)
    size_hint_y: None
    height: dp(40)

<StyledOutlineButton@Button>:
    background_color: app.colors["transparent"] if hasattr(app, 'colors') else [0, 0, 0, 0]
    color: app.colors["primary"] if hasattr(app, 'colors') else [0.23, 0.51, 0.96, 1]
    font_size: dp(14)
    size_hint_y: None
    height: dp(40)

<StyledTextInput@TextInput>:
    background_color: app.colors["background"] if hasattr(app, 'colors') else [1, 1, 1, 1]
    foreground_color: app.colors["text_primary"] if hasattr(app, 'colors') else [0.12, 0.16, 0.23, 1]
    cursor_color: app.colors["primary"] if hasattr(app, 'colors') else [0.23, 0.51, 0.96, 1]
    font_size: dp(14)
    size_hint_y: None
    height: dp(40)

<StyledLabel@Label>:
    color: app.colors["text_primary"] if hasattr(app, 'colors') else [0.12, 0.16, 0.23, 1]
    font_size: dp(14)
    text_size: self.size
    halign: 'left'
    valign: 'middle'

<StyledSecondaryLabel@Label>:
    color: app.colors["text_secondary"] if hasattr(app, 'colors') else [0.39, 0.45, 0.55, 1]
    font_size: dp(12)
    text_size: self.size
    halign: 'left'
    valign: 'middle'

<StyledSpinner@Spinner>:
    background_color: app.colors["background"] if hasattr(app, 'colors') else [1, 1, 1, 1]
    color: app.colors["text_primary"] if hasattr(app, 'colors') else [0.12, 0.16, 0.23, 1]
    font_size: dp(14)
    size_hint_y: None
    height: dp(40)

<StyledProgressBar@ProgressBar>:
    size_hint_y: None
    height: dp(20)

<StyledCheckBox@CheckBox>:
    size_hint_y: None
    height: dp(40)
    size_hint_x: None
    width: dp(40)

<StyledSlider@Slider>:
    size_hint_y: None
    height: dp(40)
'''