from PyQt5.QtGui import QFont
from src.utils.settings_manager import SettingsManager

def get_app_font():

    settings = SettingsManager()

    # lang = settings.get("language", "en")
    size = settings.get("font_size", 12)
    family = "Microsoft YaHei"
    
    return QFont(family, size)

def apply_font_to_widgets(widgets):

    font = get_app_font()

    for widget in widgets:
        if widget is None:
            continue
            
        if hasattr(widget, 'setFont'):
            widget.setFont(font)
        
        apply_font_to_children(widget, font)

def apply_font_to_children(widget, font):
    """Recursively apply font to all child widgets"""

    if widget is None:
        return
        
    # Apply font to the widget itself
    if hasattr(widget, 'setFont'):
        widget.setFont(font)
    
    # Apply font to all children
    for child in widget.findChildren(object):
        if hasattr(child, 'setFont'):
            child.setFont(font)