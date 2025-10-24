import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDesktopWidget
from PyQt5.QtCore import Qt, QByteArray, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QScreen

from src.pages.upload import UploadPage
from src.pages.library import LibraryPage
from src.pages.quiz import QuizPage
from src.pages.settings import SettingsPage

from src.utils.data_manager import DataManager
from src.utils.settings_manager import SettingsManager

from src.utils.i18n import Dict

class CustomTabBar(QWidget):
    """Page tab bar"""

    tab_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.current_tab = 0
        self.tab_enabled = [True, True, True, True]  # Enable state of tabs
        self.tab_texts = ["", "", "", ""]
        self.init_ui()
    
    def init_ui(self):

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left group: Upload, Library, Quiz
        self.left_group = QHBoxLayout()
        self.left_group.setSpacing(0)
        
        # Create tab buttons for the aboves
        self.tab_buttons = []
        for i in range(4):
            btn = QPushButton()
            btn.setStyleSheet(self.get_tab_style(i))
            btn.clicked.connect(lambda checked, idx=i: self.tab_clicked.emit(idx))
            self.tab_buttons.append(btn)
            
            if i < 3:
                self.left_group.addWidget(btn)
            else:
                pass
        
        # Add left group to main layout, add stretch to push Settings to the right
        layout.addLayout(self.left_group)
        layout.addStretch()
        layout.addWidget(self.tab_buttons[3])
        
        self.setLayout(layout)
    
    def get_tab_style(self, index):
        """Get style for tab button based on state"""

        base_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 16px 64px;
                margin: 0px;
                color: #808080;
                font-weight: normal;
                font-size: inherit;
            }
            QPushButton:hover {
                color: #000000;
                font-size: inherit;
            }
        """
        
        if index == 0:
            base_style += """
                QPushButton {
                    margin-left: 0px;
                }
            """
        
        return base_style
    
    def update_tab_style(self, index):
        """Update style for specific tab"""

        style = self.get_tab_style(index)
        
        if index == self.current_tab:
            style += """
                QPushButton {
                    color: #000000;
                    border-bottom: 3px solid #cccccc;
                }
            """
        
        if not self.tab_enabled[index]:
            style += """
                QPushButton {
                    color: #cccccc;
                    background-color: transparent;
                }
                QPushButton:hover {
                    color: #cccccc;
                }
            """
        
        self.tab_buttons[index].setStyleSheet(style)
    
    def set_current_tab(self, index):
        """Set current active tab"""

        self.current_tab = index
        for i in range(4):
            self.update_tab_style(i)
    
    def set_tab_text(self, index, text):
        """Set text for tab"""

        self.tab_texts[index] = text
        if index < len(self.tab_buttons):
            self.tab_buttons[index].setText(text)
    
    def set_tab_enabled(self, index, enabled):
        """Enable/disable tab"""

        self.tab_enabled[index] = enabled
        self.tab_buttons[index].setEnabled(enabled)
        self.update_tab_style(index)

class MahJourney(QMainWindow):

    def __init__(self):
        
        super().__init__()
        
        # Return base value
        self.BASE_WIDTH, self.BASE_HEIGHT = self.calculate_optimal_size()
        
        print(f"Detected optimal app size: {self.BASE_WIDTH}x{self.BASE_HEIGHT}")

        # App icon~
        icon_path = os.path.join(os.path.dirname(__file__), "src", "assets", "icons", "tabi.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join("src", "assets", "icons", "tabi.png")
        self.setWindowIcon(QIcon(icon_path))

        # App title, control zoom & fullscreen
        self.setWindowTitle(Dict.t("app.title"))
        self.setGeometry(100, 100, self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setMinimumSize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setMaximumSize(self.BASE_WIDTH+1800, self.BASE_HEIGHT+1200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        
        # Init managers
        self.data_manager = DataManager()
        self.settings = SettingsManager()
        
        # Create tab widget with custom tab bar
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)
        self.tab_widget.tabBar().hide()
        
        # Create custom tab bar
        self.custom_tab_bar = CustomTabBar()
        
        # Apply styling
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
                top: -1px;
            }
            QTabWidget::tab-bar {
                border: none;
            }
        """)
        
        # Create pages
        self.upload_page = UploadPage(self.data_manager)
        self.library_page = LibraryPage(self.data_manager)
        self.quiz_page = QuizPage(self.data_manager, self.settings)
        self.settings_page = SettingsPage(self.settings)
        
        # Add tabs in order: Upload, Library, Quiz, Settings
        self.tab_widget.addTab(self.upload_page, Dict.t("nav.upload"))
        self.tab_widget.addTab(self.library_page, Dict.t("nav.manage"))
        self.tab_widget.addTab(self.quiz_page, Dict.t("nav.quiz"))
        self.tab_widget.addTab(self.settings_page, Dict.t("settings.title"))
        
        # Set up custom tab bar texts
        self.custom_tab_bar.set_tab_text(0, Dict.t("nav.upload"))
        self.custom_tab_bar.set_tab_text(1, Dict.t("nav.manage"))
        self.custom_tab_bar.set_tab_text(2, Dict.t("nav.quiz"))
        self.custom_tab_bar.set_tab_text(3, Dict.t("settings.title"))
        
        # Create main layout with custom tab bar
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add custom tab bar at top, then tab widget
        main_layout.addWidget(self.custom_tab_bar)
        main_layout.addWidget(self.tab_widget)
        
        # Create central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Track edit mode, quiz mode
        self.is_edit_mode = False
        self.current_edit_entry_id = None
        self.is_quiz_mode = False
        
        # Connect
        self.connect_signals()
        self.custom_tab_bar.tab_clicked.connect(self.on_custom_tab_clicked)

        # Sync language changes to UI

        # React to language changes
        Dict.language_changed.connect(self.retranslate_ui)
        self.settings.settings_changed.connect(self.on_settings_changed)
        self.settings.settings_changed.connect(self.quiz_page.update_settings_status_labels if hasattr(self.quiz_page, 'update_settings_status_labels') else lambda *_: None)
        
        # Start with upload tab
        self.tab_widget.setCurrentIndex(0)
        self.custom_tab_bar.set_current_tab(0)  # Set custom tab bar to show Upload as selected

        self.restore_window_state()
        self.apply_font()
    
    def calculate_optimal_size(self):
        """Return the size of window"""

        try:
            # Get the screen info
            screen = QApplication.primaryScreen()
            if not screen:
                return 1400, 900  # Default, idk, may need adjust
            
            screen_size = screen.size()
            available_size = screen.availableSize()
            
            screen_width = screen_size.width()
            screen_height = screen_size.height()
            
            dpi = screen.logicalDotsPerInch()
            physical_dpi = screen.physicalDotsPerInch()
            
            scale_factor = dpi / 96.0
            
            # Return the default window size
            if screen_width >= 3840 or screen_height >= 2160:  # 4K
                if scale_factor >= 1.25:
                    base_width, base_height = 1800, 1200
                else:
                    base_width, base_height = 2000, 1400
            elif screen_width >= 2560 or screen_height >= 1440:  # 2K
                if scale_factor >= 1.25:
                    base_width, base_height = 1600, 1000
                else:
                    base_width, base_height = 1800, 1100
            else:  # <1080p
                if scale_factor >= 1.25:
                    base_width, base_height = 1400, 900
                else:
                    base_width, base_height = 1400, 900
            
            # Don't too large
            max_width = int(available_size.width() * 0.9)
            max_height = int(available_size.height() * 0.9)
            
            base_width = min(base_width, max_width)
            base_height = min(base_height, max_height)
            
            # Minimum?
            min_width, min_height = 1000, 600
            base_width = max(base_width, min_width)
            base_height = max(base_height, min_height)
            
            return base_width, base_height
            
        except Exception as e:
            print(f"Error calculating optimal size: {e}")
            return 1400, 900

    # --- Signals between pages and UI --- #
    
    def connect_signals(self):
        """Connect signals to pages"""

        # Connect library page to upload page for editing
        self.library_page.entry_edit_requested.connect(self.start_entry_edit)
        
        # Connect upload page signals
        self.upload_page.edit_mode_cancelled.connect(self.exit_edit_mode)
        self.upload_page.edit_mode_saved.connect(self.exit_edit_mode)
        
        # Connect quiz page signals
        self.quiz_page.quiz_started.connect(self.start_quiz_mode)
        self.quiz_page.quiz_ended.connect(self.end_quiz_mode)
        
        # Wire pages to settings changes (only font changes, no retranslate needed)
        self.settings.settings_changed.connect(self.upload_page.apply_font if hasattr(self.upload_page, 'apply_font') else lambda *_: None)
        self.settings.settings_changed.connect(self.library_page.apply_font if hasattr(self.library_page, 'apply_font') else lambda *_: None)
        self.settings.settings_changed.connect(self.settings_page.apply_font if hasattr(self.settings_page, 'apply_font') else lambda *_: None)
        
        # Track tab changes
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    # --- Settings --- #

    def open_settings(self):
        """Find settings tab index and switch to it"""

        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == Dict.t("settings.title"):
                self.tab_widget.setCurrentIndex(i)
                self.custom_tab_bar.set_current_tab(i)
                break

    def on_settings_changed(self, settings_dict):
        """Check if language changed"""

        if "language" in settings_dict:
            current_lang = Dict.get_language()
            new_lang = settings_dict["language"]
            if current_lang != new_lang:
                self.retranslate_ui()
        
        self.apply_font()

    # --- Window State --- #

    def closeEvent(self, event):
        """Save window state on close"""

        try:
            # Native Qt geometry (includes frame) to avoid offsets
            geom_b64 = bytes(self.saveGeometry().toBase64()).decode('utf-8')
            # Keep legacy Dict for backward compatibility
            legacy = {
                'x': int(self.x()),
                'y': int(self.y()),
                'w': int(self.width()),
                'h': int(self.height()),
            }
            self.settings.set_many({'window_geometry_b64': geom_b64, 'window_geometry': legacy})
        except Exception:
            pass
        super().closeEvent(event)

    def restore_window_state(self):
        """Restore window state to default"""

        geom_b64 = self.settings.get('window_geometry_b64')
        if isinstance(geom_b64, str) and geom_b64:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geom_b64.encode('utf-8')))
                return
            except Exception:
                pass
        # Fallback (?)
        geom = self.settings.get('window_geometry')
        if isinstance(geom, dict):
            try:
                self.setGeometry(
                    int(geom.get('x', 100)), 
                    int(geom.get('y', 100)), 
                    int(geom.get('w', self.BASE_WIDTH)), 
                    int(geom.get('h', self.BASE_HEIGHT)))
            except Exception:
                pass

    def on_tab_changed(self, index):
        """Handle tab changes"""
        
        self.custom_tab_bar.set_current_tab(index)
        self.apply_font()
    
    def on_custom_tab_clicked(self, index):
        """Handle custom tab bar clicks"""

        # Only switch if not in edit mode or quiz mode, or clicking the appropriate tab
        if not self.is_edit_mode and not self.is_quiz_mode:
            self.tab_widget.setCurrentIndex(index)
            self.custom_tab_bar.set_current_tab(index)
        elif self.is_edit_mode and index == 0:  # Can only click upload tab in edit mode
            self.tab_widget.setCurrentIndex(index)
            self.custom_tab_bar.set_current_tab(index)
        elif self.is_quiz_mode and index == 2:  # Can only click quiz tab in quiz mode
            self.tab_widget.setCurrentIndex(index)
            self.custom_tab_bar.set_current_tab(index)
    
    def start_entry_edit(self, entry_id):
        """Start editing an entry from library"""

        self.is_edit_mode = True
        self.current_edit_entry_id = entry_id
        
        # Switch to upload tab
        self.tab_widget.setCurrentIndex(0)
        self.custom_tab_bar.set_current_tab(0)
        
        # Enable edit mode in upload page
        self.upload_page.start_edit_mode(entry_id)
        
        # Disable other tabs and add forbidden cursor styling
        for i in range(self.tab_widget.count()):
            if i != 0:  # Not upload tab
                self.tab_widget.setTabEnabled(i, False)
                self.custom_tab_bar.set_tab_enabled(i, False)
        
        # Update window title
        entry_data = self.data_manager.load_entry(entry_id)
        if entry_data:
            title = entry_data.get('title', 'Unknown')
            self.setWindowTitle(f"{Dict.t("app.title")}{" - "}{Dict.t("upload.editor.title")}{title}")
        
        # Update tab title to show edit mode
        self.tab_widget.setTabText(0, Dict.t("nav.upload.edit"))
        self.custom_tab_bar.set_tab_text(0, Dict.t("nav.upload.edit"))
    
    def exit_edit_mode(self):
        """Exit edit mode and return to normal operation"""

        self.is_edit_mode = False
        self.current_edit_entry_id = None
        
        # Enable all tabs
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, True)
            self.custom_tab_bar.set_tab_enabled(i, True)
        
        # Reset window title
        self.setWindowTitle(Dict.t("app.title"))
        
        # Reset tab title to normal mode
        self.tab_widget.setTabText(0, Dict.t("nav.upload"))
        self.custom_tab_bar.set_tab_text(0, Dict.t("nav.upload"))
        
        # Exit edit mode in upload page
        self.upload_page.exit_edit_mode()
        
        # Switch back to library tab
        self.tab_widget.setCurrentIndex(1)
        self.custom_tab_bar.set_current_tab(1)
    
    def start_quiz_mode(self):
        """Start quiz mode and disable other tabs"""

        self.is_quiz_mode = True
        
        # Disable other tabs and add forbidden cursor styling
        for i in range(self.tab_widget.count()):
            if i != 2:
                self.tab_widget.setTabEnabled(i, False)
                self.custom_tab_bar.set_tab_enabled(i, False)
        
        # Switch to quiz tab
        self.tab_widget.setCurrentIndex(2)
        self.custom_tab_bar.set_current_tab(2)
    
    def end_quiz_mode(self):
        """End quiz mode and enable all tabs"""
        
        self.is_quiz_mode = False
        
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, True)
            self.custom_tab_bar.set_tab_enabled(i, True)

    # --- Language and Font --- #
        
    def retranslate_ui(self, _=None):
        """Update window title and tab names"""
        
        if not self.is_edit_mode:
            self.setWindowTitle(Dict.t("app.title"))
        
        if self.is_edit_mode:
            self.tab_widget.setTabText(0, Dict.t("nav.upload.edit"))
            self.custom_tab_bar.set_tab_text(0, Dict.t("nav.upload.edit"))
        else:
            self.tab_widget.setTabText(0, Dict.t("nav.upload"))
            self.custom_tab_bar.set_tab_text(0, Dict.t("nav.upload"))
        
        self.tab_widget.setTabText(1, Dict.t("nav.manage"))
        self.custom_tab_bar.set_tab_text(1, Dict.t("nav.manage"))
        
        self.tab_widget.setTabText(2, Dict.t("nav.quiz"))
        self.custom_tab_bar.set_tab_text(2, Dict.t("nav.quiz"))
        
        self.tab_widget.setTabText(3, Dict.t("settings.title"))
        self.custom_tab_bar.set_tab_text(3, Dict.t("settings.title"))
        
        self.reload_pages_for_language()
        self.apply_font()
    
    def reload_pages_for_language(self):
        """Reload pages to apply new language settings"""

        current_tab = self.tab_widget.currentIndex()
        
        # Store edit mode state before reloading
        was_in_edit_mode = self.is_edit_mode
        was_in_quiz_mode = self.is_quiz_mode
        current_edit_entry_id = self.current_edit_entry_id
        
        # Reload upload page
        self.upload_page.deleteLater()
        self.upload_page = UploadPage(self.data_manager)
        self.tab_widget.removeTab(0)
        self.tab_widget.insertTab(0, self.upload_page, Dict.t("nav.upload"))
        self.custom_tab_bar.set_tab_text(0, Dict.t("nav.upload"))
        
        # Reconnect upload page signals
        self.upload_page.edit_mode_cancelled.connect(self.exit_edit_mode)
        self.upload_page.edit_mode_saved.connect(self.exit_edit_mode)
        self.settings.settings_changed.connect(self.upload_page.apply_font if hasattr(self.upload_page, 'apply_font') else lambda *_: None)
        
        # Reload library page
        self.library_page.deleteLater()
        self.library_page = LibraryPage(self.data_manager)
        self.tab_widget.removeTab(1)
        self.tab_widget.insertTab(1, self.library_page, Dict.t("nav.manage"))
        self.custom_tab_bar.set_tab_text(1, Dict.t("nav.manage"))
        
        # Reconnect library page signals
        self.library_page.entry_edit_requested.connect(self.start_entry_edit)
        self.settings.settings_changed.connect(self.library_page.apply_font if hasattr(self.library_page, 'apply_font') else lambda *_: None)
        
        # Reload quiz page
        self.quiz_page.deleteLater()
        self.quiz_page = QuizPage(self.data_manager, self.settings)
        self.tab_widget.removeTab(2)
        self.tab_widget.insertTab(2, self.quiz_page, Dict.t("nav.quiz"))
        self.custom_tab_bar.set_tab_text(2, Dict.t("nav.quiz"))
        
        # Reconnect quiz page signals
        self.quiz_page.quiz_started.connect(self.start_quiz_mode)
        self.quiz_page.quiz_ended.connect(self.end_quiz_mode)
        self.settings.settings_changed.connect(self.quiz_page.apply_font if hasattr(self.quiz_page, 'apply_font') else lambda *_: None)
        self.settings.settings_changed.connect(self.quiz_page.update_settings_status_labels if hasattr(self.quiz_page, 'update_settings_status_labels') else lambda *_: None)
        
        # Reload settings page
        if hasattr(self.settings_page, 'retranslate_ui'):
            self.settings_page.retranslate_ui()
        
        # Restore edit mode state if needed
        if was_in_edit_mode and current_edit_entry_id:
            self.is_edit_mode = True
            self.current_edit_entry_id = current_edit_entry_id
            self.upload_page.start_edit_mode(current_edit_entry_id)
            
            for i in range(self.tab_widget.count()):
                if i != 0:  # Not upload tab
                    self.tab_widget.setTabEnabled(i, False)
                    self.custom_tab_bar.set_tab_enabled(i, False)
            
            entry_data = self.data_manager.load_entry(current_edit_entry_id)
            if entry_data:
                title = entry_data.get('title', 'Unknown')
                self.setWindowTitle(f"{Dict.t('app.title')} - {Dict.t('upload.editor.title')}{title}")
            
            self.tab_widget.setTabText(0, Dict.t("nav.upload.edit"))
            self.custom_tab_bar.set_tab_text(0, Dict.t("nav.upload.edit"))
        
        # Restore quiz mode state if needed
        if was_in_quiz_mode:
            self.is_quiz_mode = True
            
            for i in range(self.tab_widget.count()):
                if i != 2:  # Not quiz tab
                    self.tab_widget.setTabEnabled(i, False)
                    self.custom_tab_bar.set_tab_enabled(i, False)
        
        # Restore current tab
        self.tab_widget.setCurrentIndex(current_tab)
        self.custom_tab_bar.set_current_tab(current_tab)
    
    def apply_font(self):
        """Apply current font settings to tab widget and all pages"""

        from src.utils.format_applier import apply_font_to_widgets
        
        apply_font_to_widgets([self.tab_widget])
        
        if hasattr(self, 'upload_page') and hasattr(self.upload_page, 'apply_font'):
            self.upload_page.apply_font()
        if hasattr(self, 'library_page') and hasattr(self.library_page, 'apply_font'):
            self.library_page.apply_font()
        if hasattr(self, 'quiz_page') and hasattr(self.quiz_page, 'apply_font'):
            self.quiz_page.apply_font()
        if hasattr(self, 'settings_page') and hasattr(self.settings_page, 'apply_font'):
            self.settings_page.apply_font()

if __name__ == "__main__":

    app = QApplication(sys.argv)

    # Load font
    _settings = SettingsManager()
    _settings.apply_to_app(app)

    # Use saved language setting or default English
    from src.utils.i18n import Dict as _dict
    saved_language = _settings.get("language", "en")
    _dict.set_language(saved_language)

    '''if _settings.get("font_size", 12) != 12:
        _settings.set_many({"font_size": 12})'''

    window = MahJourney()
    window.show()
    sys.exit(app.exec_())