from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QCheckBox
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices

from src.utils.i18n import Dict
from src.utils.format_applier import apply_font_to_widgets

class SettingsPage(QWidget):

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.init_ui()
        Dict.language_changed.connect(self.retranslate_ui)

    def init_ui(self):

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(80, 80, 80, 80)

        # Left side - icon and author
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignCenter)
        
        # GitHub icon..?
        github_label = QLabel()
        '''icon_file = "src/assets/icons/github.png"'''
        icon_file = "src/assets/icons/0itmub.png"
        github_pixmap = QPixmap(icon_file)
        if not github_pixmap.isNull():
            github_pixmap = github_pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            github_label.setPixmap(github_pixmap)
        github_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(github_label)

        # Version text
        version_label = QLabel("MahJourney v0.9")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("Qlabel{padding:8;}")
        left_layout.addWidget(version_label)
        
        # Intro text
        self.intro_label = QLabel(Dict.t("app.intro"))
        self.intro_label.setAlignment(Qt.AlignCenter)
        self.intro_label.setStyleSheet("QLabel { padding: 8px; color: #0066cc; text-decoration: underline; }")
        self.intro_label.setCursor(Qt.PointingHandCursor)
        
        def open_github_link(event):
            if event.button() == Qt.LeftButton:
                QDesktopServices.openUrl(QUrl("https://github.com/AokoC/MahJourney"))
            else:
                QLabel.mousePressEvent(self.intro_label, event)
        
        self.intro_label.mousePressEvent = open_github_link
        left_layout.addWidget(self.intro_label)

        # Author text
        author_label = QLabel(Dict.t("app.author"))
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("Qlabel{padding:8;}")
        left_layout.addWidget(author_label)
        
        left_container.setLayout(left_layout)
        
        # Right side - Settings
        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)
        
        # Settings content container
        settings_content = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(50)
        
        # Create a centered container for aligned settings
        settings_container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.addStretch()
        
        # Inner layout for aligned settings
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(25)
        
        # Language
        row_lang = QHBoxLayout()
        self.lbl_lang = QLabel(Dict.t("settings.language"))
        self.lbl_lang.setStyleSheet("QLabel{padding:8;}")
        self.lbl_lang.setAlignment(Qt.AlignRight)
        self.lbl_lang.setMinimumWidth(220)
        self.cmb_lang = QComboBox()
        self.cmb_lang.setStyleSheet("QComboBox{padding:8;}")
        self.cmb_lang.setFixedWidth(220)
        self.cmb_lang.addItem(Dict.t("lang.zh_Hans"), "zh_Hans")
        self.cmb_lang.addItem(Dict.t("lang.zh_Hant"), "zh_Hant")
        self.cmb_lang.addItem(Dict.t("lang.jp"), "jp")
        self.cmb_lang.addItem(Dict.t("lang.en"), "en")
        langs = [self.cmb_lang.itemData(i) for i in range(self.cmb_lang.count())]
        cur = self.settings.get("language", "en")
        idx = langs.index(cur) if cur in langs else 0
        self.cmb_lang.setCurrentIndex(idx)
        self.cmb_lang.currentTextChanged.connect(self.on_language_changed)
        row_lang.addWidget(self.lbl_lang)
        row_lang.addWidget(self.cmb_lang)
        inner_layout.addLayout(row_lang)

        # Font size
        row_size = QHBoxLayout()
        self.lbl_size = QLabel(Dict.t("settings.size"))
        self.lbl_size.setStyleSheet("QLabel{padding:8;}")
        self.lbl_size.setAlignment(Qt.AlignRight)
        self.lbl_size.setMinimumWidth(220)
        self.spn_size = QSpinBox()
        self.spn_size.setStyleSheet("QSpinBox{padding:8;}")
        self.spn_size.setFixedWidth(220)
        self.spn_size.setRange(6, 18)
        self.spn_size.setValue(int(self.settings.get("font_size", 12)))
        self.spn_size.valueChanged.connect(self.on_font_size_changed)
        row_size.addWidget(self.lbl_size)
        row_size.addWidget(self.spn_size)
        inner_layout.addLayout(row_size)

        # Career stats
        row_career = QHBoxLayout()
        self.lbl_career = QLabel(Dict.t("settings.career_stats"))
        self.lbl_career.setAlignment(Qt.AlignRight)
        self.lbl_career.setStyleSheet("QLabel{padding:8;}")
        self.lbl_career.setMinimumWidth(220)
        self.chk_career = QCheckBox()
        # self.chk_career.setStyleSheet("QCheckBox{padding:8;}")
        self.chk_career.setChecked(self.settings.get("career_stats", True))
        self.chk_career.toggled.connect(self.on_career_stats_changed)
        row_career.addWidget(self.lbl_career)
        row_career.addWidget(self.chk_career)
        inner_layout.addLayout(row_career)

        # Quiz timer
        row_timer = QHBoxLayout()
        self.lbl_timer = QLabel(Dict.t("settings.timer"))
        self.lbl_timer.setAlignment(Qt.AlignRight)
        self.lbl_timer.setStyleSheet("QLabel{padding:8;}")
        self.lbl_timer.setMinimumWidth(220)
        self.chk_timer = QCheckBox()
        self.chk_timer.setChecked(self.settings.get("timer", False))
        self.chk_timer.toggled.connect(self.on_timer_changed)
        row_timer.addWidget(self.lbl_timer)
        row_timer.addWidget(self.chk_timer)
        inner_layout.addLayout(row_timer)
        
        # Endless
        row_endless = QHBoxLayout()
        self.lbl_endless = QLabel(Dict.t("settings.endless"))
        self.lbl_endless.setAlignment(Qt.AlignRight)
        self.lbl_endless.setStyleSheet("QLabel{padding:8;}")
        self.lbl_endless.setMinimumWidth(220)
        self.chk_endless = QCheckBox()
        self.chk_endless.setChecked(self.settings.get("endless", False))
        self.chk_endless.toggled.connect(self.on_endless_changed)
        row_endless.addWidget(self.lbl_endless)
        row_endless.addWidget(self.chk_endless)
        inner_layout.addLayout(row_endless)
        
        settings_container.setLayout(inner_layout)
        container_layout.addWidget(settings_container)
        container_layout.addStretch()
        
        settings_layout.addLayout(container_layout)

        # Reset button with normal size
        reset_button_layout = QHBoxLayout()
        reset_button_layout.addStretch()
        self.btn_reset_window = QPushButton(Dict.t("settings.reset_window"))
        self.btn_reset_window.setStyleSheet("QPushButton{padding:8;}")
        self.btn_reset_window.clicked.connect(self.on_reset_window)
        reset_button_layout.addWidget(self.btn_reset_window)
        reset_button_layout.addStretch()
        settings_layout.addLayout(reset_button_layout)
        
        # Size hint label below reset button
        size_hint_layout = QHBoxLayout()
        size_hint_layout.addStretch()
        self.size_hint_label = QLabel(Dict.t("settings.size_hint"))
        self.size_hint_label.setAlignment(Qt.AlignCenter)
        self.size_hint_label.setStyleSheet("QLabel{padding:8; color: #666666;}")
        size_hint_layout.addWidget(self.size_hint_label)
        size_hint_layout.addStretch()
        settings_layout.addLayout(size_hint_layout)
        
        settings_content.setLayout(settings_layout)
        right_layout.addWidget(settings_content)
        right_container.setLayout(right_layout)
        
        # Add both containers to main layout
        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(right_container, 1)
        
        self.setLayout(main_layout)

    def on_language_changed(self, text):
        """Find the language code for the selected text"""

        for i in range(self.cmb_lang.count()):
            if self.cmb_lang.itemText(i) == text:
                lang_code = self.cmb_lang.itemData(i)
                # Only update if language actually changed
                if Dict.get_language() != lang_code:
                    self.settings.set_many({"language": lang_code})
                    Dict.set_language(lang_code)
                break

    def on_font_size_changed(self, value):

        self.settings.set_many({"font_size": value})

    def on_career_stats_changed(self, checked):

        self.settings.set_many({"career_stats": checked})

    def on_timer_changed(self, checked):

        self.settings.set_many({"timer": checked})

    def on_endless_changed(self, checked):

        self.settings.set_many({"endless": checked})

    def on_reset_window(self):
        """Reset window geometry and font size"""

        self.settings.set_many({
            "window_geometry_b64": "",
            "window_geometry": {},
            "font_size": 12
        })
        
        # Reset font size spinbox
        self.spn_size.setValue(12)
        
        self.apply_font()
        
        # Get the main window and reset its geometry
        main_window = self.parent()
        while main_window:
            if hasattr(main_window, 'setGeometry') and hasattr(main_window, 'BASE_WIDTH'):
                # This is the main window
                main_window.setGeometry(100, 100, main_window.BASE_WIDTH, main_window.BASE_HEIGHT)
                # Apply font to the entire application
                main_window.apply_font()
                break
            main_window = main_window.parent()
        
        # Also apply font to the QApplication
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            self.settings.apply_to_app(app)

    def retranslate_ui(self, _=None):

        self.lbl_lang.setText(Dict.t("settings.language"))
        self.lbl_size.setText(Dict.t("settings.size"))
        self.lbl_career.setText(Dict.t("settings.career_stats"))
        self.lbl_timer.setText(Dict.t("settings.timer"))
        self.lbl_endless.setText(Dict.t("settings.endless"))
        self.btn_reset_window.setText(Dict.t("settings.reset_window"))
        self.size_hint_label.setText(Dict.t("settings.size_hint"))

        self.cmb_lang.setItemText(0, Dict.t("lang.zh_Hans"))
        self.cmb_lang.setItemText(1, Dict.t("lang.zh_Hant"))
        self.cmb_lang.setItemText(2, Dict.t("lang.jp"))
        self.cmb_lang.setItemText(3, Dict.t("lang.en"))
        
        if hasattr(self, 'intro_label'):
            self.intro_label.setText(Dict.t("app.intro"))
        
        author_labels = self.findChildren(QLabel)
        for label in author_labels:
            if label.text() == Dict.t("app.author") or "作者" in label.text() or "Author" in label.text():
                label.setText(Dict.t("app.author"))

    def apply_font(self, _=None):
        
        widgets = [
            self.btn_reset_window, 
            self.lbl_lang, self.cmb_lang,
            self.lbl_size, self.spn_size,
            self.lbl_career, self.chk_career,
            self.lbl_timer, self.chk_timer,
            self.lbl_endless, self.chk_endless,
            self.size_hint_label
        ]
        apply_font_to_widgets(widgets)