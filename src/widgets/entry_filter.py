from PyQt5.QtWidgets import (   QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QComboBox, QPushButton, QWidget, QSizePolicy, 
                                QLineEdit, QStyle, QScrollArea, QCheckBox, 
                                QRadioButton, QButtonGroup, QGroupBox, QFrame, QSlider)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QIntValidator, QIcon
from datetime import datetime

from src.utils.i18n import Dict
from src.utils.format_applier import apply_font_to_widgets
from src.widgets.hint_dialog import StyledMessageBox

class NoWheelSlider(QSlider):
    """Disable wheel"""
    
    def wheelEvent(self, event):
        event.ignore()

class EntryFilterDialog(QDialog):
    """Dialog for Entry Filter with different conditions"""
    
    def __init__(self, parent=None):

        super().__init__(parent)
        self.setWindowTitle(Dict.t("library.filter.title"))
        self.setModal(True)
        
        self.filter_state = {
            'text_contains': {'text': '', 'fields': []},
            'text_excludes': {'text': '', 'fields': []},
            'source': [],
            'players': [],
            'image': [],
            'wind': [],
            'self_wind': [],
            'game': [],
            'difficulty_min': 0,
            'difficulty_max': 100,
            'accuracy_min': 0,
            'accuracy_max': 100,
            'start_date': None,
            'end_date': None,
            'logic_mode': 'OR',
            'negate': False
        }
        
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.init_ui()
        self.apply_font()
        self.setup_connections()
    
    def init_ui(self):

        # Main
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Scroll area for all groupbox
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        
        # Different filter's groupbox
        self.create_text_filter_section(scroll_layout)
        self.create_basic_info_filter_section(scroll_layout)
        self.create_numerical_filter_section(scroll_layout)
        self.create_date_filter_section(scroll_layout)
        self.create_advanced_filter_section(scroll_layout)
        
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        main_layout.addWidget(scroll_area)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # self.setMinimumWidth(760)

        button_layout = QHBoxLayout()
        
        # Reset
        self.reset_btn = QPushButton(Dict.t("action.reset"))
        self.reset_btn.setStyleSheet("QPushButton{padding:8;}")
        self.reset_btn.clicked.connect(self.reset_filters)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # Info
        self.filter_help_btn = QPushButton()
        self.filter_help_btn.setFixedSize(30, 30)
        self.filter_help_btn.setIcon(QIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation)))
        self.filter_help_btn.setStyleSheet("QPushButton { border: none; background-color: transparent; } QPushButton:hover { background-color: #e0e0e0; }")
        self.filter_help_btn.clicked.connect(self.show_filter_help)
        button_layout.addWidget(self.filter_help_btn)
        
        # OK
        self.ok_btn = QPushButton(Dict.t("common.ok"))
        self.ok_btn.setStyleSheet("QPushButton{padding:8;}")
        self.ok_btn.clicked.connect(self.accept_filters)
        button_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_text_filter_section(self, parent_layout):
        """Text filter"""

        group = QGroupBox(Dict.t("filter.text_filter"))
        self.group_text_filter = group
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Includes
        contains_layout = QHBoxLayout()
        self.contains_label = QLabel(Dict.t("filter.contains"))
        self.contains_label.setStyleSheet("QLabel{padding:8; color: #585858;}")
        contains_layout.addWidget(self.contains_label)
        
        self.contains_input = QLineEdit()
        self.contains_input.setPlaceholderText(Dict.t("filter.contains.placeholder"))
        self.contains_input.setStyleSheet("QLineEdit{padding:8;}")
        contains_layout.addWidget(self.contains_input)
        
        layout.addLayout(contains_layout)
        
        # Includes' multiple choice
        contains_checkboxes = QHBoxLayout()
        self.contains_title_cb = QCheckBox(Dict.t("filter.title"))
        self.contains_intro_cb = QCheckBox(Dict.t("filter.intro"))
        self.contains_notes_cb = QCheckBox(Dict.t("filter.notes"))
        
        contains_checkboxes.addWidget(self.contains_title_cb)
        contains_checkboxes.addWidget(self.contains_intro_cb)
        contains_checkboxes.addWidget(self.contains_notes_cb)
        contains_checkboxes.addStretch()
        
        layout.addLayout(contains_checkboxes)
        
        # Excludes
        excludes_layout = QHBoxLayout()
        self.excludes_label = QLabel(Dict.t("filter.excludes"))
        self.excludes_label.setStyleSheet("QLabel{padding:8; color: #585858;}")
        excludes_layout.addWidget(self.excludes_label)
        
        self.excludes_input = QLineEdit()
        self.excludes_input.setPlaceholderText(Dict.t("filter.excludes.placeholder"))
        self.excludes_input.setStyleSheet("QLineEdit{padding:8;}")
        excludes_layout.addWidget(self.excludes_input)
        
        layout.addLayout(excludes_layout)
        
        # Excludes' multiple choice
        excludes_checkboxes = QHBoxLayout()
        self.excludes_title_cb = QCheckBox(Dict.t("filter.title"))
        self.excludes_intro_cb = QCheckBox(Dict.t("filter.intro"))
        self.excludes_notes_cb = QCheckBox(Dict.t("filter.notes"))
        
        excludes_checkboxes.addWidget(self.excludes_title_cb)
        excludes_checkboxes.addWidget(self.excludes_intro_cb)
        excludes_checkboxes.addWidget(self.excludes_notes_cb)
        excludes_checkboxes.addStretch()
        
        layout.addLayout(excludes_checkboxes)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_basic_info_filter_section(self, parent_layout):
        """Basic info filter"""

        group = QGroupBox(Dict.t("filter.basic_info_filter"))
        self.group_basic_info = group
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout()
        layout.setSpacing(30)
        
        # Source, players, image
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        
        # Source
        source_layout = QVBoxLayout()
        self.source_title = QLabel(Dict.t("upload.source"))
        self.source_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        source_checkboxes = QVBoxLayout()
        source_checkboxes.setSpacing(5)
        self.source_mahjong_soul_cb = QCheckBox(Dict.t("source.mahjong_soul"))
        self.source_tenhou_cb = QCheckBox(Dict.t("source.tenhou"))
        self.source_riichi_city_cb = QCheckBox(Dict.t("source.riichi_city"))
        self.source_exercises_cb = QCheckBox(Dict.t("source.exercises"))
        self.source_others_cb = QCheckBox(Dict.t("source.others"))
        
        source_checkboxes.addWidget(self.source_mahjong_soul_cb)
        source_checkboxes.addWidget(self.source_tenhou_cb)
        source_checkboxes.addWidget(self.source_riichi_city_cb)
        source_checkboxes.addWidget(self.source_exercises_cb)
        source_checkboxes.addWidget(self.source_others_cb)
        
        source_layout.addWidget(self.source_title)
        source_layout.addLayout(source_checkboxes)
        row1_layout.addLayout(source_layout, 1)
        
        # Players
        players_layout = QVBoxLayout()
        self.players_title = QLabel(Dict.t("upload.players"))
        self.players_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        players_checkboxes = QVBoxLayout()
        players_checkboxes.setSpacing(5)
        self.players_four_cb = QCheckBox(Dict.t("players.four"))
        self.players_three_cb = QCheckBox(Dict.t("players.three"))
        self.players_other_cb = QCheckBox(Dict.t("players.other"))
        
        players_checkboxes.addWidget(self.players_four_cb)
        players_checkboxes.addWidget(self.players_three_cb)
        players_checkboxes.addWidget(self.players_other_cb)
        
        players_layout.addWidget(self.players_title)
        players_layout.addLayout(players_checkboxes)
        row1_layout.addLayout(players_layout, 1)

        # Image
        image_layout = QVBoxLayout()
        self.image_title = QLabel(Dict.t("library.image"))
        self.image_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        image_checkboxes = QVBoxLayout()
        image_checkboxes.setSpacing(5)
        self.image_have_cb = QCheckBox(Dict.t("common.have"))
        self.image_no_have_cb = QCheckBox(Dict.t("common.noHave"))
        image_checkboxes.addWidget(self.image_have_cb)
        image_checkboxes.addWidget(self.image_no_have_cb)
        
        image_layout.addWidget(self.image_title)
        image_layout.addLayout(image_checkboxes)
        row1_layout.addLayout(image_layout, 1)

        row1_layout.setAlignment(Qt.AlignTop)
        row1_layout.setAlignment(source_layout, Qt.AlignTop)
        row1_layout.setAlignment(players_layout, Qt.AlignTop)
        row1_layout.setAlignment(image_layout, Qt.AlignTop)
        layout.addLayout(row1_layout)
        
        # Wind, self wind, game
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        
        # Wind
        wind_layout = QVBoxLayout()
        self.wind_title = QLabel(Dict.t("info.wind"))
        self.wind_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        wind_checkboxes = QVBoxLayout()
        wind_checkboxes.setSpacing(5)
        self.wind_east_cb = QCheckBox(Dict.t("info.east"))
        self.wind_south_cb = QCheckBox(Dict.t("info.south"))
        self.wind_west_cb = QCheckBox(Dict.t("info.west"))
        self.wind_north_cb = QCheckBox(Dict.t("info.north"))
        
        wind_checkboxes.addWidget(self.wind_east_cb)
        wind_checkboxes.addWidget(self.wind_south_cb)
        wind_checkboxes.addWidget(self.wind_west_cb)
        wind_checkboxes.addWidget(self.wind_north_cb)
        
        wind_layout.addWidget(self.wind_title)
        wind_layout.addLayout(wind_checkboxes)
        row2_layout.addLayout(wind_layout, 1)

        # Self Wind
        swind_layout = QVBoxLayout()
        self.swind_title = QLabel(Dict.t("info.swind.title"))
        self.swind_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        swind_checkboxes = QVBoxLayout()
        swind_checkboxes.setSpacing(5)
        self.swind_east_cb = QCheckBox(Dict.t("info.east"))
        self.swind_south_cb = QCheckBox(Dict.t("info.south"))
        self.swind_west_cb = QCheckBox(Dict.t("info.west"))
        self.swind_north_cb = QCheckBox(Dict.t("info.north"))
        
        swind_checkboxes.addWidget(self.swind_east_cb)
        swind_checkboxes.addWidget(self.swind_south_cb)
        swind_checkboxes.addWidget(self.swind_west_cb)
        swind_checkboxes.addWidget(self.swind_north_cb)
        
        swind_layout.addWidget(self.swind_title)
        swind_layout.addLayout(swind_checkboxes)
        row2_layout.addLayout(swind_layout, 1)
        
        # Game
        game_layout = QVBoxLayout()
        self.game_title = QLabel(Dict.t("info.game"))
        self.game_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        game_checkboxes = QVBoxLayout()
        game_checkboxes.setSpacing(5)
        self.game_1_cb = QCheckBox("1")
        self.game_2_cb = QCheckBox("2")
        self.game_3_cb = QCheckBox("3")
        self.game_4_cb = QCheckBox("4")
        
        game_checkboxes.addWidget(self.game_1_cb)
        game_checkboxes.addWidget(self.game_2_cb)
        game_checkboxes.addWidget(self.game_3_cb)
        game_checkboxes.addWidget(self.game_4_cb)
        
        game_layout.addWidget(self.game_title)
        game_layout.addLayout(game_checkboxes)
        row2_layout.addLayout(game_layout, 1)

        row2_layout.setAlignment(Qt.AlignTop)
        row2_layout.setAlignment(wind_layout, Qt.AlignTop)
        row2_layout.setAlignment(game_layout, Qt.AlignTop)
        layout.addLayout(row2_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_numerical_filter_section(self, parent_layout):
        """Value filter"""

        group = QGroupBox(Dict.t("filter.numerical_filter"))
        self.group_numerical = group
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        numeric_row = QHBoxLayout()
        numeric_row.setSpacing(24)
        numeric_row.setContentsMargins(0, 0, 0, 0)

        # Title
        left_col = QVBoxLayout()
        left_col.setSpacing(18)
        left_col.setContentsMargins(0, 0, 0, 0)
        self.difficulty_title = QLabel(Dict.t("upload.difficulty"))
        self.difficulty_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        self.accuracy_title = QLabel(Dict.t("career.accuracy"))
        self.accuracy_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        left_col.addWidget(self.difficulty_title)
        left_col.addWidget(self.accuracy_title)

        right_col = QVBoxLayout()
        right_col.setSpacing(10)
        right_col.setContentsMargins(0, 0, 0, 0)

        # Min diff
        diff_min_row = QHBoxLayout()
        diff_min_row.addWidget(QLabel(Dict.t("library.difficulty_min")))
        self.difficulty_min_slider = NoWheelSlider(Qt.Horizontal)
        self.difficulty_min_slider.setMinimum(0)
        self.difficulty_min_slider.setMaximum(100)
        self.difficulty_min_slider.setValue(0)
        self.difficulty_min_slider.setMinimumWidth(300)
        self.difficulty_min_slider.setStyleSheet(
            "QSlider::handle:horizontal"
            "{background: #007BFF; width: 20px; height: 20px; margin: -7px 0; border-radius: 10px;}"
            "QSlider::handle:horizontal:hover"
            "{background: #0056b3;}"
            "QSlider::groove:horizontal"
            "{background: #E0E0E0; height: 6px; margin: 0px; border-radius: 3px;}"
            "QSlider::sub-page:horizontal"
            "{background: #007BFF; border-radius: 3px;}"
            "QSlider::add-page:horizontal"
            "{background: #E0E0E0; border-radius: 3px;}"
        )
        self.difficulty_min_value = QLabel("0")
        self.difficulty_min_value.setFixedWidth(75)
        self.difficulty_min_slider.valueChanged.connect(lambda v: self.difficulty_min_value.setText(str(v)))
        diff_min_row.addWidget(self.difficulty_min_slider, 1)
        diff_min_row.addWidget(self.difficulty_min_value)
        right_col.addLayout(diff_min_row)

        # Max diff
        diff_max_row = QHBoxLayout()
        diff_max_row.addWidget(QLabel(Dict.t("library.difficulty_max")))
        self.difficulty_max_slider = NoWheelSlider(Qt.Horizontal)
        self.difficulty_max_slider.setMinimum(0)
        self.difficulty_max_slider.setMaximum(100)
        self.difficulty_max_slider.setValue(100)
        self.difficulty_max_slider.setMinimumWidth(300)
        self.difficulty_max_slider.setStyleSheet(
            "QSlider::handle:horizontal"
            "{background: #007BFF; width: 20px; height: 20px; margin: -7px 0; border-radius: 10px;}"
            "QSlider::handle:horizontal:hover"
            "{background: #0056b3;}"
            "QSlider::groove:horizontal"
            "{background: #E0E0E0; height: 6px; margin: 0px; border-radius: 3px;}"
            "QSlider::sub-page:horizontal"
            "{background: #007BFF; border-radius: 3px;}"
            "QSlider::add-page:horizontal"
            "{background: #E0E0E0; border-radius: 3px;}"
        )
        self.difficulty_max_value = QLabel("100")
        self.difficulty_max_value.setFixedWidth(75)
        self.difficulty_max_slider.valueChanged.connect(lambda v: self.difficulty_max_value.setText(str(v)))
        diff_max_row.addWidget(self.difficulty_max_slider, 1)
        diff_max_row.addWidget(self.difficulty_max_value)
        right_col.addLayout(diff_max_row)
        
        # Min accu
        acc_min_row = QHBoxLayout()
        acc_min_row.addWidget(QLabel(Dict.t("library.accuracy_min")))
        self.accuracy_min_slider = NoWheelSlider(Qt.Horizontal)
        self.accuracy_min_slider.setMinimum(0)
        self.accuracy_min_slider.setMaximum(100)
        self.accuracy_min_slider.setValue(0)
        self.accuracy_min_slider.setMinimumWidth(300)
        self.accuracy_min_slider.setStyleSheet(
            "QSlider::handle:horizontal"
            "{background: #007BFF; width: 20px; height: 20px; margin: -7px 0; border-radius: 10px;}"
            "QSlider::handle:horizontal:hover"
            "{background: #0056b3;}"
            "QSlider::groove:horizontal"
            "{background: #E0E0E0; height: 6px; margin: 0px; border-radius: 3px;}"
            "QSlider::sub-page:horizontal"
            "{background: #007BFF; border-radius: 3px;}"
            "QSlider::add-page:horizontal"
            "{background: #E0E0E0; border-radius: 3px;}"
        )
        self.accuracy_min_value = QLabel("0%")
        self.accuracy_min_value.setFixedWidth(75)
        self.accuracy_min_slider.valueChanged.connect(lambda v: self.accuracy_min_value.setText(f"{v}%"))
        self.accuracy_min_slider.valueChanged.connect(lambda _: self.validate_inputs())
        acc_min_row.addWidget(self.accuracy_min_slider, 1)
        acc_min_row.addWidget(self.accuracy_min_value)
        right_col.addLayout(acc_min_row)

        # Max accu
        acc_max_row = QHBoxLayout()
        acc_max_row.addWidget(QLabel(Dict.t("library.accuracy_max")))
        self.accuracy_max_slider = NoWheelSlider(Qt.Horizontal)
        self.accuracy_max_slider.setMinimum(0)
        self.accuracy_max_slider.setMaximum(100)
        self.accuracy_max_slider.setValue(100)
        self.accuracy_max_slider.setMinimumWidth(300)
        self.accuracy_max_slider.setStyleSheet(
            "QSlider::handle:horizontal"
            "{background: #007BFF; width: 20px; height: 20px; margin: -7px 0; border-radius: 10px;}"
            "QSlider::handle:horizontal:hover"
            "{background: #0056b3;}"
            "QSlider::groove:horizontal"
            "{background: #E0E0E0; height: 6px; margin: 0px; border-radius: 3px;}"
            "QSlider::sub-page:horizontal"
            "{background: #007BFF; border-radius: 3px;}"
            "QSlider::add-page:horizontal"
            "{background: #E0E0E0; border-radius: 3px;}"
        )
        self.accuracy_max_value = QLabel("100%")
        self.accuracy_max_value.setFixedWidth(75)
        self.accuracy_max_slider.valueChanged.connect(lambda v: self.accuracy_max_value.setText(f"{v}%"))
        self.accuracy_max_slider.valueChanged.connect(lambda _: self.validate_inputs())
        acc_max_row.addWidget(self.accuracy_max_slider, 1)
        acc_max_row.addWidget(self.accuracy_max_value)
        right_col.addLayout(acc_max_row)

        numeric_row.addLayout(left_col)
        numeric_row.addLayout(right_col)
        layout.addLayout(numeric_row)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_date_filter_section(self, parent_layout):
        """Date filter"""

        group = QGroupBox(Dict.t("filter.date_filter"))
        self.group_date = group
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Start date
        start_date_layout = QHBoxLayout()
        '''start_date_layout.addWidget(QLabel(Dict.t("library.start_date")))'''
        
        self.start_date_title = QLabel(Dict.t("library.start_date"))
        self.start_date_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        
        self.start_year = QLineEdit()
        self.start_year.setPlaceholderText("YYYY")
        self.start_year.setFixedWidth(125)
        self.start_year.setMaxLength(4)
        self.start_year.setValidator(QIntValidator(0, 9999))
        self.start_year.setStyleSheet("QLineEdit{padding:8;}")
        
        self.start_month = QLineEdit()
        self.start_month.setPlaceholderText("MM")
        self.start_month.setFixedWidth(75)
        self.start_month.setMaxLength(2)
        self.start_month.setValidator(QIntValidator(1, 12))
        self.start_month.setStyleSheet("QLineEdit{padding:8;}")
        
        self.start_day = QLineEdit()
        self.start_day.setPlaceholderText("DD")
        self.start_day.setFixedWidth(75)
        self.start_day.setMaxLength(2)
        self.start_day.setValidator(QIntValidator(1, 31))
        self.start_day.setStyleSheet("QLineEdit{padding:8;}")
        
        start_date_layout.addWidget(self.start_year)
        start_date_layout.addWidget(self.start_month)
        start_date_layout.addWidget(self.start_day)
        start_date_layout.addStretch()
        
        start_date_layout.insertWidget(0, self.start_date_title)
        layout.addLayout(start_date_layout)
        
        # End date
        end_date_layout = QHBoxLayout()
        '''end_date_layout.addWidget(QLabel(Dict.t("library.end_date")))'''
        
        self.end_date_title = QLabel(Dict.t("library.end_date"))
        self.end_date_title.setStyleSheet("QLabel{padding:8; color: #585858;}")
        
        self.end_year = QLineEdit()
        self.end_year.setPlaceholderText("YYYY")
        self.end_year.setFixedWidth(125)
        self.end_year.setMaxLength(4)
        self.end_year.setValidator(QIntValidator(0, 9999))
        self.end_year.setStyleSheet("QLineEdit{padding:8;}")
        
        self.end_month = QLineEdit()
        self.end_month.setPlaceholderText("MM")
        self.end_month.setFixedWidth(75)
        self.end_month.setMaxLength(2)
        self.end_month.setValidator(QIntValidator(1, 12))
        self.end_month.setStyleSheet("QLineEdit{padding:8;}")
        
        self.end_day = QLineEdit()
        self.end_day.setPlaceholderText("DD")
        self.end_day.setFixedWidth(75)
        self.end_day.setMaxLength(2)
        self.end_day.setValidator(QIntValidator(1, 31))
        self.end_day.setStyleSheet("QLineEdit{padding:8;}")
        
        end_date_layout.addWidget(self.end_year)
        end_date_layout.addWidget(self.end_month)
        end_date_layout.addWidget(self.end_day)
        end_date_layout.addStretch()
        
        end_date_layout.insertWidget(0, self.end_date_title)
        layout.addLayout(end_date_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_advanced_filter_section(self, parent_layout):
        """Advanced (logic) filter"""

        group = QGroupBox(Dict.t("filter.advanced_filter"))
        self.group_advanced = group
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout()
        layout.setSpacing(15)

        logic_layout = QVBoxLayout()
        
        self.logic_button_group = QButtonGroup()
        
        self.or_radio = QRadioButton(Dict.t("filter.or"))
        self.or_radio.setChecked(True)
        '''self.or_radio.setToolTip(Dict.t("filter.or.tooltip"))'''
        
        self.and_radio = QRadioButton(Dict.t("filter.and"))
        '''self.and_radio.setToolTip(Dict.t("filter.and.tooltip"))'''
        
        self.logic_button_group.addButton(self.or_radio, 1)
        self.logic_button_group.addButton(self.and_radio, 0)
        
        # OR, AND
        logic_layout.addWidget(self.or_radio)
        logic_layout.addWidget(self.and_radio)
        
        # NOT
        self.not_checkbox = QCheckBox(Dict.t("filter.not"))
        '''self.not_checkbox.setToolTip(Dict.t("filter.not.tooltip"))'''
        
        logic_layout.addWidget(self.not_checkbox)
        
        layout.addLayout(logic_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def setup_connections(self):
        """Connections"""

        # Text filter
        self.contains_input.textChanged.connect(self.update_label_colors)
        self.excludes_input.textChanged.connect(self.update_label_colors)
        
        # Checkbox
        for checkbox in [self.contains_title_cb, self.contains_intro_cb, self.contains_notes_cb,
                        self.excludes_title_cb, self.excludes_intro_cb, self.excludes_notes_cb,
                        self.source_mahjong_soul_cb, self.source_tenhou_cb, self.source_riichi_city_cb,
                        self.source_exercises_cb, self.source_others_cb,
                        self.players_four_cb, self.players_three_cb, self.players_other_cb,
                        self.image_have_cb, self.image_no_have_cb,
                        self.wind_east_cb, self.wind_south_cb, self.wind_west_cb, self.wind_north_cb,
                        self.swind_east_cb, self.swind_south_cb, self.swind_west_cb, self.swind_north_cb,
                        self.game_1_cb, self.game_2_cb, self.game_3_cb, self.game_4_cb]:
            checkbox.toggled.connect(self.update_label_colors)
        
        # Slider
        self.difficulty_min_slider.valueChanged.connect(lambda _: self.on_difficulty_changed(self.difficulty_min_slider.value(), self.difficulty_max_slider.value()))
        self.difficulty_min_slider.valueChanged.connect(lambda _: self.validate_inputs())
        self.difficulty_max_slider.valueChanged.connect(lambda _: self.on_difficulty_changed(self.difficulty_min_slider.value(), self.difficulty_max_slider.value()))
        self.difficulty_max_slider.valueChanged.connect(lambda _: self.validate_inputs())
        self.accuracy_min_slider.valueChanged.connect(lambda _: self.on_accuracy_changed(self.accuracy_min_slider.value(), self.accuracy_max_slider.value()))
        self.accuracy_max_slider.valueChanged.connect(lambda _: self.on_accuracy_changed(self.accuracy_min_slider.value(), self.accuracy_max_slider.value()))
        
        # Date
        for date_input in [self.start_year, self.start_month, self.start_day,
                          self.end_year, self.end_month, self.end_day]:
            date_input.textChanged.connect(self.update_label_colors)
            date_input.textChanged.connect(self.validate_inputs)
    
    def on_difficulty_changed(self, min_val, max_val):
        """Handle change in diff"""

        self.difficulty_min_value.setText(str(min_val))
        self.difficulty_max_value.setText(str(max_val))
        self.update_label_colors()
    
    def on_accuracy_changed(self, min_val, max_val):
        """Handle change in accu"""

        self.accuracy_min_value.setText(f"{min_val}%")
        self.accuracy_max_value.setText(f"{max_val}%")
        self.update_label_colors()
    
    def update_label_colors(self):
        """Change color when applied or not"""
        
        # Text filter
        text_contains_active = (self.contains_input.text().strip() and 
                               (self.contains_title_cb.isChecked() or 
                                self.contains_intro_cb.isChecked() or 
                                self.contains_notes_cb.isChecked()))
        
        text_excludes_active = (self.excludes_input.text().strip() and 
                               (self.excludes_title_cb.isChecked() or 
                                self.excludes_intro_cb.isChecked() or 
                                self.excludes_notes_cb.isChecked()))
        
        # Info filter
        source_active = any([self.source_mahjong_soul_cb.isChecked(),
                           self.source_tenhou_cb.isChecked(),
                           self.source_riichi_city_cb.isChecked(),
                           self.source_exercises_cb.isChecked(),
                           self.source_others_cb.isChecked()])
        
        players_active = any([self.players_four_cb.isChecked(),
                            self.players_three_cb.isChecked(),
                            self.players_other_cb.isChecked()])
        
        image_active = any([self.image_have_cb.isChecked(),
                          self.image_no_have_cb.isChecked()])
        
        wind_active = any([self.wind_east_cb.isChecked(),
                         self.wind_south_cb.isChecked(),
                         self.wind_west_cb.isChecked(),
                         self.wind_north_cb.isChecked()])
        swind_active = any([self.swind_east_cb.isChecked(),
                         self.swind_south_cb.isChecked(),
                         self.swind_west_cb.isChecked(),
                         self.swind_north_cb.isChecked()])
        
        game_active = any([self.game_1_cb.isChecked(),
                         self.game_2_cb.isChecked(),
                         self.game_3_cb.isChecked(),
                         self.game_4_cb.isChecked()])
        
        # Value filter
        difficulty_active = not (self.difficulty_min_slider.value() == 0 and self.difficulty_max_slider.value() == 100)
        accuracy_active = not (self.accuracy_min_slider.value() == 0 and self.accuracy_max_slider.value() == 100)
        
        # Date filter
        start_date = self.get_date_from_inputs(
            self.start_year.text(), self.start_month.text(), self.start_day.text()
        )
        end_date = self.get_date_from_inputs(
            self.end_year.text(), self.end_month.text(), self.end_day.text()
        )
        
        start_date_active = start_date is not None
        end_date_active = end_date is not None
        
        active_color = "#0056b3"
        inactive_color = "#585858"

        def apply_title_color(label, is_active):

            if label is None:
                return
            color = active_color if is_active else inactive_color
            label.setStyleSheet(f"QLabel{{padding:8; color: {color};}}")

        apply_title_color(getattr(self, 'contains_label', None), text_contains_active)
        apply_title_color(getattr(self, 'excludes_label', None), text_excludes_active)

        apply_title_color(getattr(self, 'source_title', None), source_active)
        apply_title_color(getattr(self, 'players_title', None), players_active)
        apply_title_color(getattr(self, 'image_title', None), image_active)
        apply_title_color(getattr(self, 'wind_title', None), wind_active)
        apply_title_color(getattr(self, 'game_title', None), game_active)
        apply_title_color(getattr(self, 'swind_title', None), swind_active)

        apply_title_color(getattr(self, 'difficulty_title', None), difficulty_active)
        apply_title_color(getattr(self, 'accuracy_title', None), accuracy_active)

        apply_title_color(getattr(self, 'start_date_title', None), start_date_active)
        apply_title_color(getattr(self, 'end_date_title', None), end_date_active)
    
    def show_filter_help(self):

        StyledMessageBox.information(self, Dict.t("library.filter.help.title"), Dict.t("library.filter.help.content")).exec_()
    
    def reset_filters(self):
        """Reset all filter conditions to default"""

        self.contains_input.clear()
        self.excludes_input.clear()
        self.contains_title_cb.setChecked(False)
        self.contains_intro_cb.setChecked(False)
        self.contains_notes_cb.setChecked(False)
        self.excludes_title_cb.setChecked(False)
        self.excludes_intro_cb.setChecked(False)
        self.excludes_notes_cb.setChecked(False)

        for checkbox in [self.source_mahjong_soul_cb, self.source_tenhou_cb, self.source_riichi_city_cb,
                        self.source_exercises_cb, self.source_others_cb,
                        self.players_four_cb, self.players_three_cb, self.players_other_cb,
                        self.image_have_cb, self.image_no_have_cb,
                        self.wind_east_cb, self.wind_south_cb, self.wind_west_cb, self.wind_north_cb,
                        self.swind_east_cb, self.swind_south_cb, self.swind_west_cb, self.swind_north_cb,
                        self.game_1_cb, self.game_2_cb, self.game_3_cb, self.game_4_cb]:
            checkbox.setChecked(False)
        
        self.difficulty_min_slider.setValue(0)
        self.difficulty_max_slider.setValue(100)
        self.accuracy_min_slider.setValue(0)
        self.accuracy_max_slider.setValue(100)

        for date_input in [self.start_year, self.start_month, self.start_day,
                          self.end_year, self.end_month, self.end_day]:
            date_input.clear()

        self.or_radio.setChecked(True)
        self.not_checkbox.setChecked(False)
        
        self.update_label_colors()
    
    def accept_filters(self):
        """Accept filter conditions and close dialog"""

        # Collect those filter groups one by one
        contains_fields = []
        if self.contains_title_cb.isChecked():
            contains_fields.append('title')
        if self.contains_intro_cb.isChecked():
            contains_fields.append('intro')
        if self.contains_notes_cb.isChecked():
            contains_fields.append('notes')
        
        excludes_fields = []
        if self.excludes_title_cb.isChecked():
            excludes_fields.append('title')
        if self.excludes_intro_cb.isChecked():
            excludes_fields.append('intro')
        if self.excludes_notes_cb.isChecked():
            excludes_fields.append('notes')
        
        self.filter_state['text_contains'] = {
            'text': self.contains_input.text().strip(),
            'fields': contains_fields
        }
        self.filter_state['text_excludes'] = {
            'text': self.excludes_input.text().strip(),
            'fields': excludes_fields
        }
        
        source_values = []
        if self.source_mahjong_soul_cb.isChecked():
            source_values.append('source.mahjong_soul')
        if self.source_tenhou_cb.isChecked():
            source_values.append('source.tenhou')
        if self.source_riichi_city_cb.isChecked():
            source_values.append('source.riichi_city')
        if self.source_exercises_cb.isChecked():
            source_values.append('source.exercises')
        if self.source_others_cb.isChecked():
            source_values.append('source.others')
        
        players_values = []
        if self.players_four_cb.isChecked():
            players_values.append('players.four')
        if self.players_three_cb.isChecked():
            players_values.append('players.three')
        if self.players_other_cb.isChecked():
            players_values.append('players.other')
        
        image_values = []
        if self.image_have_cb.isChecked():
            image_values.append('common.have')
        if self.image_no_have_cb.isChecked():
            image_values.append('common.noHave')
        
        wind_values = []
        if self.wind_east_cb.isChecked():
            wind_values.append('info.east')
        if self.wind_south_cb.isChecked():
            wind_values.append('info.south')
        if self.wind_west_cb.isChecked():
            wind_values.append('info.west')
        if self.wind_north_cb.isChecked():
            wind_values.append('info.north')
        swind_values = []
        if self.swind_east_cb.isChecked():
            swind_values.append('info.east')
        if self.swind_south_cb.isChecked():
            swind_values.append('info.south')
        if self.swind_west_cb.isChecked():
            swind_values.append('info.west')
        if self.swind_north_cb.isChecked():
            swind_values.append('info.north')
        
        game_values = []
        if self.game_1_cb.isChecked():
            game_values.append('1')
        if self.game_2_cb.isChecked():
            game_values.append('2')
        if self.game_3_cb.isChecked():
            game_values.append('3')
        if self.game_4_cb.isChecked():
            game_values.append('4')
        
        self.filter_state['source'] = source_values
        self.filter_state['players'] = players_values
        self.filter_state['image'] = image_values
        self.filter_state['wind'] = wind_values
        self.filter_state['game'] = game_values
        self.filter_state['self_wind'] = swind_values
        
        difficulty_min, difficulty_max = self.difficulty_min_slider.value(), self.difficulty_max_slider.value()
        accuracy_min, accuracy_max = self.accuracy_min_slider.value(), self.accuracy_max_slider.value()
        
        self.filter_state['difficulty_min'] = difficulty_min
        self.filter_state['difficulty_max'] = difficulty_max
        self.filter_state['accuracy_min'] = accuracy_min
        self.filter_state['accuracy_max'] = accuracy_max
        
        self.filter_state['start_date'] = self.get_date_from_inputs(
            self.start_year.text(), self.start_month.text(), self.start_day.text()
        )
        self.filter_state['end_date'] = self.get_date_from_inputs(
            self.end_year.text(), self.end_month.text(), self.end_day.text()
        )
        
        self.filter_state['logic_mode'] = 'OR' if self.or_radio.isChecked() else 'AND'
        self.filter_state['negate'] = self.not_checkbox.isChecked()
        
        self.accept()
    
    def get_date_from_inputs(self, year, month, day):

        try:
            year = year.strip()
            month = month.strip()
            day = day.strip()
            
            if not (year and month and day):
                return None
            
            year = int(year)
            month = int(month)
            day = int(day)
            
            # Validate date
            if year < 0 or year > 9999:
                return None
            if month < 1 or month > 12:
                return None
            if day < 1 or day > 31:
                return None
            
            return datetime(year, month, day)
        except (ValueError, TypeError):
            return None
    
    def validate_inputs(self):
        """Validate inputs for value; disable / enable OK button"""

        is_valid = True
        
        # Date
        start_date = self.get_date_from_inputs(
            self.start_year.text(), self.start_month.text(), self.start_day.text()
        )
        end_date = self.get_date_from_inputs(
            self.end_year.text(), self.end_month.text(), self.end_day.text()
        )
        
        # If both not default, then start date should before end date
        if start_date and end_date and start_date > end_date:
            is_valid = False
        
        # If one box not default, then remaining 2 boxes of the related date also need not default
        start_has_input = any([
            self.start_year.text().strip(),
            self.start_month.text().strip(),
            self.start_day.text().strip()
        ])
        end_has_input = any([
            self.end_year.text().strip(),
            self.end_month.text().strip(),
            self.end_day.text().strip()
        ])
        
        # If one date not default, then all should be valid
        if start_has_input and start_date is None:
            is_valid = False
        if end_has_input and end_date is None:
            is_valid = False
        
        # Diff / accu should be max > min
        if self.difficulty_min_slider.value() > self.difficulty_max_slider.value():
            is_valid = False
        if self.accuracy_min_slider.value() > self.accuracy_max_slider.value():
            is_valid = False

        self.ok_btn.setEnabled(is_valid)
    
    def get_filter_state(self):

        return self.filter_state.copy()
    
    def set_filter_state(self, state):
        """Set filter state"""

        self.filter_state = state.copy()
        
        # Set filter for different groups
        self.contains_input.setText(self.filter_state['text_contains']['text'])
        self.excludes_input.setText(self.filter_state['text_excludes']['text'])
        
        for field in self.filter_state['text_contains']['fields']:
            if field == 'title':
                self.contains_title_cb.setChecked(True)
            elif field == 'intro':
                self.contains_intro_cb.setChecked(True)
            elif field == 'notes':
                self.contains_notes_cb.setChecked(True)
        
        for field in self.filter_state['text_excludes']['fields']:
            if field == 'title':
                self.excludes_title_cb.setChecked(True)
            elif field == 'intro':
                self.excludes_intro_cb.setChecked(True)
            elif field == 'notes':
                self.excludes_notes_cb.setChecked(True)
        
        for source in self.filter_state['source']:
            if source == 'source.mahjong_soul':
                self.source_mahjong_soul_cb.setChecked(True)
            elif source == 'source.tenhou':
                self.source_tenhou_cb.setChecked(True)
            elif source == 'source.riichi_city':
                self.source_riichi_city_cb.setChecked(True)
            elif source == 'source.exercises':
                self.source_exercises_cb.setChecked(True)
            elif source == 'source.others':
                self.source_others_cb.setChecked(True)
        
        for players in self.filter_state['players']:
            if players == 'players.four':
                self.players_four_cb.setChecked(True)
            elif players == 'players.three':
                self.players_three_cb.setChecked(True)
            elif players == 'players.other':
                self.players_other_cb.setChecked(True)
        
        for image in self.filter_state['image']:
            if image == 'common.have':
                self.image_have_cb.setChecked(True)
            elif image == 'common.noHave':
                self.image_no_have_cb.setChecked(True)
        
        for wind in self.filter_state['wind']:
            if wind == 'info.east':
                self.wind_east_cb.setChecked(True)
            elif wind == 'info.south':
                self.wind_south_cb.setChecked(True)
            elif wind == 'info.west':
                self.wind_west_cb.setChecked(True)
            elif wind == 'info.north':
                self.wind_north_cb.setChecked(True)
        for swind in self.filter_state.get('self_wind', []):
            if swind == 'info.east':
                self.swind_east_cb.setChecked(True)
            elif swind == 'info.south':
                self.swind_south_cb.setChecked(True)
            elif swind == 'info.west':
                self.swind_west_cb.setChecked(True)
            elif swind == 'info.north':
                self.swind_north_cb.setChecked(True)
        
        for game in self.filter_state['game']:
            if game == '1':
                self.game_1_cb.setChecked(True)
            elif game == '2':
                self.game_2_cb.setChecked(True)
            elif game == '3':
                self.game_3_cb.setChecked(True)
            elif game == '4':
                self.game_4_cb.setChecked(True)
        
        self.difficulty_min_slider.setValue(self.filter_state['difficulty_min'])
        self.difficulty_max_slider.setValue(self.filter_state['difficulty_max'])
        self.accuracy_min_slider.setValue(self.filter_state['accuracy_min'])
        self.accuracy_max_slider.setValue(self.filter_state['accuracy_max'])
        
        if self.filter_state.get('start_date'):
            date = self.filter_state['start_date']
            if isinstance(date, datetime):
                self.start_year.setText(str(date.year))
                self.start_month.setText(str(date.month).zfill(2))
                self.start_day.setText(str(date.day).zfill(2))
        
        if self.filter_state.get('end_date'):
            date = self.filter_state['end_date']
            if isinstance(date, datetime):
                self.end_year.setText(str(date.year))
                self.end_month.setText(str(date.month).zfill(2))
                self.end_day.setText(str(date.day).zfill(2))
        
        if self.filter_state['logic_mode'] == 'OR':
            self.or_radio.setChecked(True)
        else:
            self.and_radio.setChecked(True)
        
        self.not_checkbox.setChecked(self.filter_state['negate'])

        self.update_label_colors()
    
    def apply_font(self):

        widgets = [
            self.reset_btn, self.ok_btn, self.filter_help_btn,
            self.contains_input, self.excludes_input,
            self.start_year, self.start_month, self.start_day,
            self.end_year, self.end_month, self.end_day
        ]
        
        labels = self.findChildren(QLabel)
        checkboxes = self.findChildren(QCheckBox)
        radio_buttons = self.findChildren(QRadioButton)
        
        widgets.extend(labels)
        widgets.extend(checkboxes)
        widgets.extend(radio_buttons)
        
        apply_font_to_widgets(widgets)

    def showEvent(self, event: QEvent):
        """Called when the page becomes visible to refresh page"""

        super().showEvent(event)
        self.setFixedSize(self.width()+50, self.height())