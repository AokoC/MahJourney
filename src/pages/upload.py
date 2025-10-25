import os
import re
from datetime import datetime
from PyQt5.QtWidgets import (   QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QFrame, QButtonGroup, QRadioButton, 
                                QLineEdit, QTextEdit, QFileDialog, QMessageBox,
                                QGroupBox, QGridLayout, QApplication, QSizePolicy,
                                QSlider, QStyle, QComboBox, QSpinBox, QDateTimeEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent, QRegExpValidator, QIcon
from PyQt5.QtCore import QMimeData, QRegExp
from collections import Counter

from src.utils.i18n import Dict
from src.utils.validators import Validator
from src.utils.format_applier import apply_font_to_widgets

from src.widgets.tile_selector import TileSelector
from src.widgets.hint_dialog import StyledMessageBox

class UploadPage(QWidget):

    back_clicked = pyqtSignal()
    upload_complete = pyqtSignal()
    edit_mode_cancelled = pyqtSignal()
    edit_mode_saved = pyqtSignal()
    
    def __init__(self, data_manager):

        super().__init__()
        self.data_manager = data_manager
        self.current_image_path = None

        # Initialize hands and answer data
        self.current_hands = ""
        self.current_answer = ""
        self.current_dora = ""
        
        # Edit mode tracking
        self.is_edit_mode = False
        self.current_edit_entry_id = None
        self.original_entry_data = None
        
        # Track temporary files for cleanup; register cleanup on application exit
        self.temp_files = []
        import atexit
        atexit.register(self.cleanup_temp_files)
        
        self.init_ui()
        self.setFocusPolicy(Qt.StrongFocus)
    
    def init_ui(self):
        
        root_layout = QVBoxLayout()
        root_layout.setSpacing(12)

        main_layout = QHBoxLayout()

        # --------- Left --------- #

        left_frame = QFrame()
        left_layout = QVBoxLayout()
        
        # --- Create Time section --- #
        self.create_time_group = QGroupBox(Dict.t("upload.editor.create_time"))
        self.create_time_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        create_time_layout = QHBoxLayout()
        
        # Create time datetime picker
        self.create_time_input = QDateTimeEdit()
        self.create_time_input.setStyleSheet("QDateTimeEdit{padding:8;}")
        self.create_time_input.setDateTime(QDateTime.currentDateTime())
        self.create_time_input.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        create_time_layout.addWidget(self.create_time_input)
        
        self.create_time_group.setLayout(create_time_layout)
        left_layout.addWidget(self.create_time_group)
        
        # --- Title section --- #
        self.title_group = QGroupBox(Dict.t("upload.title"))
        title_layout = QVBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setStyleSheet("QLineEdit{padding:8;}")
        self.title_input.setPlaceholderText(Dict.t("upload.title_placeholder"))
        title_layout.addWidget(self.title_input)
        self.title_group.setLayout(title_layout)
        left_layout.addWidget(self.title_group)
        
        # --- Source & Players section --- #
        self.source_players_group = QGroupBox(Dict.t("upload.background"))
        self.source_players_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        source_players_layout = QHBoxLayout()

        # Source combobox
        self.combobox_source = QComboBox()
        self.combobox_source.setStyleSheet("QComboBox{padding:8;}")

        source_keys = [
            "source.mahjong_soul",
            "source.tenhou", 
            "source.riichi_city",
            "source.exercises",
            "source.others"
        ]
        self.combobox_source.addItem("")
        for key in source_keys:
            self.combobox_source.addItem(Dict.t(key))
        self.source_label = QLabel(Dict.t("upload.source"))
        self.source_label.setStyleSheet("QLabel{padding:8;}")
        source_players_layout.addWidget(self.source_label)
        source_players_layout.addWidget(self.combobox_source, 1)

        # Players combobox
        self.combobox_players = QComboBox()
        self.combobox_players.setStyleSheet("QComboBox{padding:8;}")
        players_keys = [
            "players.four",
            "players.three",
            "players.other"
        ]
        self.combobox_players.addItem("")
        for key in players_keys:
            self.combobox_players.addItem(Dict.t(key))
        self.combobox_players.currentTextChanged.connect(self.on_players_changed)
        self.players_label = QLabel(Dict.t("upload.players"))
        self.players_label.setStyleSheet("QLabel{padding:8;}")
        source_players_layout.addWidget(self.players_label)
        source_players_layout.addWidget(self.combobox_players, 1)

        self.source_players_group.setLayout(source_players_layout)
        left_layout.addWidget(self.source_players_group)
        
        # --- Difficulty section --- #
        self.difficulty_group = QGroupBox(Dict.t("upload.difficulty"))
        self.difficulty_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        difficulty_layout = QHBoxLayout()
        self.difficulty_slider = QSlider(Qt.Horizontal)
        self.difficulty_slider.setMinimum(0)
        self.difficulty_slider.setMaximum(100)
        self.difficulty_slider.setValue(0)
        self.lbl_difficulty_value = QLabel("0")
        self.difficulty_slider.valueChanged.connect(lambda v: self.lbl_difficulty_value.setText(str(v)))
        self.difficulty_slider.setStyleSheet(
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
        self.lbl_difficulty_value.setFixedWidth(40)

        # Help button for difficulty
        self.difficulty_help_btn = QPushButton()
        self.difficulty_help_btn.setFixedSize(30, 30)
        self.difficulty_help_btn.setIcon(QIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation)))
        self.difficulty_help_btn.setStyleSheet("QPushButton { border: none; background-color: transparent; } QPushButton:hover { background-color: #e0e0e0; }")
        self.difficulty_help_btn.clicked.connect(self.show_difficulty_help)

        difficulty_layout.addWidget(self.difficulty_slider)
        difficulty_layout.addWidget(self.lbl_difficulty_value)
        difficulty_layout.addWidget(self.difficulty_help_btn)

        self.difficulty_group.setLayout(difficulty_layout)
        left_layout.addWidget(self.difficulty_group)

        # --- Game info section --- #
        self.game_info_group = QGroupBox(Dict.t("info.title"))
        self.game_info_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        game_info_layout = QHBoxLayout()

        # Wind combobox
        self.combobox_wind = QComboBox()
        self.combobox_wind.setStyleSheet("QComboBox{padding:8;}")
        wind_keys = ["info.east", "info.south", "info.west", "info.north"]
        for key in wind_keys:
            self.combobox_wind.addItem(Dict.t(key))
        game_info_layout.addWidget(self.combobox_wind, 1)

        # Game combobox  
        self.combobox_game = QComboBox()
        self.combobox_game.setStyleSheet("QComboBox{padding:8;}")
        for key in ["1", "2", "3", "4"]:
            self.combobox_game.addItem(key)
        game_info_layout.addWidget(self.combobox_game, 1)

        # "Game" wording
        self.combobox_game_label = QLabel(Dict.t("info.game"))
        self.combobox_game_label.setStyleSheet("QLabel{padding:8;}")
        game_info_layout.addWidget(self.combobox_game_label, 1)

        # Honba input
        self.input_honba = QLineEdit()
        self.input_honba.setStyleSheet("QLineEdit{padding:8;}")
        self.input_honba.setPlaceholderText("")
        self.input_honba.setMaxLength(2)
        regex = QRegExp("[0-9]{0,2}")
        validator = QRegExpValidator(regex)
        self.input_honba.setValidator(validator)
        game_info_layout.addWidget(self.input_honba, 1)

        # "Honba" wording
        self.combobox_honba_label = QLabel(Dict.t("info.honba"))
        self.combobox_honba_label.setStyleSheet("QLabel{padding:8;}")
        game_info_layout.addWidget(self.combobox_honba_label, 1)

        game_info_layout.addStretch(2)

        # Self wind combobox
        self.combobox_swind = QComboBox()
        self.combobox_swind.setStyleSheet("QComboBox{padding:8;}")
        swind_keys = ["info.east", "info.south", "info.west", "info.north"]
        for key in swind_keys:
            self.combobox_swind.addItem(Dict.t(key))
        game_info_layout.addWidget(self.combobox_swind, 1)

        # "Self wind" wording
        self.combobox_swind_label = QLabel(Dict.t("info.swind"))
        self.combobox_swind_label.setStyleSheet("QLabel{padding:8;}")
        game_info_layout.addWidget(self.combobox_swind_label, 1)

        # Turn input
        self.input_turn = QLineEdit()
        self.input_turn.setStyleSheet("QLineEdit{padding:8;}")
        self.input_turn.setPlaceholderText("")
        self.input_turn.setMaxLength(2)
        self.input_turn.setValidator(validator)
        game_info_layout.addWidget(self.input_turn, 1)

        # "Turn" wording
        self.combobox_turn_label = QLabel(Dict.t("info.turn"))
        self.combobox_turn_label.setStyleSheet("QLabel{padding:8;}")
        game_info_layout.addWidget((self.combobox_turn_label), 1)

        self.game_info_group.setLayout(game_info_layout)
        left_layout.addWidget(self.game_info_group)
        
        # --- Dora section --- #
        self.dora_group = QGroupBox(Dict.t("dora.title"))
        self.dora_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        dora_layout = QHBoxLayout()

        # Dora display label
        self.dora_display = QLabel("")
        self.dora_display.setStyleSheet("border: 1px solid #ccc; padding: 8px; min-height: 20px;")
        self.dora_display.setWordWrap(True)
        dora_layout.addWidget(self.dora_display, stretch=1)

        # Select button
        self.btn_select_dora = QPushButton(Dict.t("action.select"))
        self.btn_select_dora.setStyleSheet("QPushButton{padding:8;}")
        self.btn_select_dora.clicked.connect(self.open_dora_selector)
        dora_layout.addWidget(self.btn_select_dora)

        # Help button
        self.dora_help_btn = QPushButton()
        self.dora_help_btn.setFixedSize(30, 30)
        self.dora_help_btn.setIcon(QIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation)))
        self.dora_help_btn.setStyleSheet("QPushButton { border: none; background-color: transparent; } QPushButton:hover { background-color: #e0e0e0; }")
        self.dora_help_btn.clicked.connect(self.show_dora_help)
        dora_layout.addWidget(self.dora_help_btn)

        self.dora_group.setLayout(dora_layout)
        left_layout.addWidget(self.dora_group)
        
        # --- Hands section --- #
        self.hands_group = QGroupBox(Dict.t("upload.hands"))
        self.hands_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        hands_layout = QHBoxLayout()
        
        # Hands display label
        self.hands_display = QLabel("")
        self.hands_display.setStyleSheet("border: 1px solid #ccc; padding: 8px; min-height: 20px;")
        self.hands_display.setWordWrap(True)
        hands_layout.addWidget(self.hands_display, stretch=1)
        
        # Select button
        self.btn_select_hands = QPushButton(Dict.t("action.select"))
        self.btn_select_hands.setStyleSheet("QPushButton{padding:8;}")
        self.btn_select_hands.clicked.connect(self.open_hands_selector)
        hands_layout.addWidget(self.btn_select_hands)
        
        # Help button
        self.hands_help_btn = QPushButton()
        self.hands_help_btn.setFixedSize(30, 30)
        self.hands_help_btn.setIcon(QIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation)))
        self.hands_help_btn.setStyleSheet("QPushButton { border: none; background-color: transparent; } QPushButton:hover { background-color: #e0e0e0; }")
        self.hands_help_btn.clicked.connect(self.show_hands_help)
        hands_layout.addWidget(self.hands_help_btn)
        
        self.hands_group.setLayout(hands_layout)
        left_layout.addWidget(self.hands_group)

        # --- Answer section --- #
        self.answer_group = QGroupBox(Dict.t("upload.answer"))
        self.answer_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        answer_layout = QVBoxLayout()

        # Answer choices (radio buttons)
        choices_layout = QGridLayout()
        self.answer_buttons = QButtonGroup(self)
        answer_keys = [
            "answer.discard",
            "answer.riichi",
            "answer.agari",
            "answer.ankan",
            "answer.skip",
            "answer.chi", 
            "answer.pon",
            "answer.kan"
        ]
        for i, key in enumerate(answer_keys):
            btn = QRadioButton(Dict.t(key))
            self.answer_buttons.addButton(btn, i)
            
            # Layout: 4, 4
            if i < 4:
                choices_layout.addWidget(btn, 0, i)
            else:
                choices_layout.addWidget(btn, 1, i-4)
                
            # Connect radio button change event
            btn.toggled.connect(self.update_select_button_state)
            
        answer_layout.addLayout(choices_layout)

        # Single answer string
        answer_input_layout = QHBoxLayout()

        # Answer display label
        self.answer_display = QLabel("")
        self.answer_display.setStyleSheet("border: 1px solid #ccc; padding: 8px; min-height: 20px;")
        self.answer_display.setWordWrap(True)
        answer_input_layout.addWidget(self.answer_display, stretch=1)

        # Select button
        self.btn_select_answer = QPushButton(Dict.t("action.select"))
        self.btn_select_answer.setStyleSheet("QPushButton{padding:8;}")
        self.btn_select_answer.clicked.connect(self.open_answer_selector)
        answer_input_layout.addWidget(self.btn_select_answer)

        # Help button
        self.answer_help_btn = QPushButton()
        self.answer_help_btn.setFixedSize(30, 30)
        self.answer_help_btn.setIcon(QIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation)))
        self.answer_help_btn.setStyleSheet("QPushButton { border: none; background-color: transparent; } QPushButton:hover { background-color: #e0e0e0; }")
        self.answer_help_btn.clicked.connect(self.show_answer_help)
        answer_input_layout.addWidget(self.answer_help_btn)

        answer_layout.addLayout(answer_input_layout)
        self.answer_group.setLayout(answer_layout)
        left_layout.addWidget(self.answer_group)

        self.answer_input = QLineEdit()
        self.answer_input.setVisible(False)
        
        # Add stretch after all components to push them to top
        left_layout.addStretch()
        left_frame.setLayout(left_layout)
        
        # --------- Right --------- #

        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        
        # --- Image section --- #
        self.image_label = QLabel()
        self.image_label.setMinimumSize(380, 250)
        self.image_label.setMaximumHeight(250)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; color: #666;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText(Dict.t("upload.hint"))
        self.image_label.setWordWrap(True)
        self.image_label.setCursor(Qt.PointingHandCursor)
        self.image_label.mousePressEvent = self._on_image_click
        
        self._apply_hint_font()
        # Store original pixmap to avoid blur on resize
        self.original_pixmap = None

        # Clear (cross) button overlay on image (hidden until image loaded)
        self.btn_clear_image = QPushButton("✕", self.image_label)
        self.btn_clear_image.setVisible(False)
        self.btn_clear_image.setStyleSheet("QPushButton{"
                "border:none;"
                "background:rgba(0,0,0,0.4);"
                "color:white;"
                "border-radius:18px;"
                "padding:0;"
                "font-size:18px;"
                "}"
                "QPushButton:hover{"
                "background:rgba(196,43,28,1);"
                "}"
        )
        self.btn_clear_image.setFixedSize(36, 36)
        self.btn_clear_image.clicked.connect(self._on_clear_image)
        self.btn_clear_image.setFocusPolicy(Qt.NoFocus)

        # Open folder button (only shown in edit mode with existing image)
        self.btn_open_folder = QPushButton("...", self.image_label)
        self.btn_open_folder.setVisible(False)
        self.btn_open_folder.setStyleSheet("QPushButton{"
                "border:none;"
                "background:rgba(0,0,0,0.4);"
                "color:white;"
                "border-radius:18px;"
                "padding:0;"
                "font-size:18px;"
                "}"
                "QPushButton:hover{"
                "background:rgba(0,123,255,1);"
                "}"
        )
        self.btn_open_folder.setFixedSize(36, 36)
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        self.btn_open_folder.setFocusPolicy(Qt.NoFocus)
        
        right_layout.addWidget(self.image_label)
        
        # --- Intro section --- #
        self.intro_group = QGroupBox(Dict.t("upload.intro"))
        intro_layout = QVBoxLayout()
        self.intro_input = QTextEdit()
        self.intro_input.setPlaceholderText(Dict.t("upload.intro_placeholder"))
        intro_layout.addWidget(self.intro_input)
        self.intro_group.setLayout(intro_layout)
        right_layout.addWidget(self.intro_group)

        # --- Notes section --- #
        self.notes_group = QGroupBox(Dict.t("upload.notes"))
        notes_layout = QVBoxLayout()
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(Dict.t("upload.notes_placeholder"))
        notes_layout.addWidget(self.notes_input)
        self.notes_group.setLayout(notes_layout)
        right_layout.addWidget(self.notes_group)
        
        # --- Career Stats section --- #
        self.career_group = QGroupBox()
        self.career_group.setVisible(False)  # Hidden by default
        career_layout = QHBoxLayout()
        
        # Encounter
        career_layout.addWidget(QLabel(Dict.t("career.encounter")))
        self.encounter_input = QLineEdit()
        self.encounter_input.setReadOnly(True)
        self.encounter_input.setStyleSheet("background-color: #f0f0f0;")
        career_layout.addWidget(self.encounter_input)
        
        # Correct
        career_layout.addWidget(QLabel(Dict.t("career.correct")))
        self.correct_input = QLineEdit()
        self.correct_input.setReadOnly(True)
        self.correct_input.setStyleSheet("background-color: #f0f0f0;")
        career_layout.addWidget(self.correct_input)
        
        # Accuracy
        career_layout.addWidget(QLabel(Dict.t("career.accuracy")))
        self.accuracy_input = QLineEdit()
        self.accuracy_input.setReadOnly(True)
        self.accuracy_input.setStyleSheet("background-color: #f0f0f0;")
        career_layout.addWidget(self.accuracy_input)
        
        self.career_group.setLayout(career_layout)
        right_layout.addWidget(self.career_group)

        # --- Reset & Save buttons --- #
        actions_row = QHBoxLayout()

        self.btn_reset = QPushButton(Dict.t("action.reset"))
        self.btn_reset.setStyleSheet("QPushButton{padding:8;}")
        self.btn_reset.clicked.connect(self.reset_all)
        actions_row.addWidget(self.btn_reset)

        # Reset Career button (edit mode)
        self.btn_reset_career = QPushButton(Dict.t("career.edit.resetCareer"))
        self.btn_reset_career.setStyleSheet("QPushButton{padding:8;}")
        self.btn_reset_career.setVisible(False)
        self.btn_reset_career.clicked.connect(self.reset_career)
        actions_row.addWidget(self.btn_reset_career)

        actions_row.addStretch()

        # Cancel button (edit mode)
        self.btn_cancel = QPushButton(Dict.t("career.edit.cancel"))
        self.btn_cancel.setStyleSheet("QPushButton{padding:8;}")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.cancel_edit)
        actions_row.addWidget(self.btn_cancel)

        self.btn_save = QPushButton(Dict.t("action.save"))
        self.btn_save.setStyleSheet("QPushButton{padding:8;}")
        self.btn_save.clicked.connect(self.save_data)
        actions_row.addWidget(self.btn_save)
        right_layout.addLayout(actions_row)
        right_frame.setLayout(right_layout)
        
        # Add widget
        main_layout.addWidget(left_frame, stretch=5)
        main_layout.addWidget(right_frame, stretch=5)
        root_layout.addLayout(main_layout)
        
        self.setLayout(root_layout)
        
        self.hands_input = QLineEdit()
        self.hands_input.setVisible(False)
        self.dora_input = QLineEdit()
        self.dora_input.setVisible(False)
        root_layout.addWidget(self.hands_input)
        root_layout.addWidget(self.dora_input)
        root_layout.addWidget(self.answer_input)

        # --------- Updates --------- #

        # Update answer, dora select button; answer options
        self.update_select_button_state()
        self.update_answer_options_state()

        self.hands_input.textChanged.connect(self.on_hands_changed)
        self.hands_input.textChanged.connect(self.update_select_button_state)

        for btn in self.answer_buttons.buttons():
            btn.toggled.connect(self.update_select_button_state)
        
        # Apply font settings to buttons after layout is complete
        QApplication.processEvents()
        self.apply_font()

    # --- Tile Selector Methods --- #

    def open_hands_selector(self):
        """Call TileSelector with "hands" param"""

        dora_tiles = TileSelector.parse_tiles_string(self.current_dora) if self.current_dora else []
        
        # Check if 3P mode
        is_three_player = self.combobox_players.currentText() == Dict.t("players.three")
        
        selector = TileSelector(    self, mode="hands", 
                                    current_selection=self.current_hands, 
                                    dora=self.current_dora,
                                    is_three_player=is_three_player)
        
        selector.dora_tiles = dora_tiles
        
        selector.selection_completed.connect(self.on_hands_selected)
        selector.exec_()

    def open_answer_selector(self):
        """Call TileSelector with answer-related param"""

        has_hands = bool(self.hands_input.text().strip())
        is_skip = False
        
        answer_action_for_selector = None
        checked_button = self.answer_buttons.checkedButton()
        if checked_button:
            answer_action = checked_button.text()
            if answer_action and answer_action == Dict.t("answer.skip"):
                is_skip = True
            elif answer_action == Dict.t("answer.chi"):
                answer_action_for_selector = "chi"
            elif answer_action == Dict.t("answer.pon"):
                answer_action_for_selector = "pon" 
            elif answer_action == Dict.t("answer.kan"):
                answer_action_for_selector = "kan"
        
        if not has_hands:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("answer.hint.noHands")).exec_()
            return
        elif is_skip:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("answer.hint.skip")).exec_()
            return
        
        hands_for_selector = self.current_hands if self.current_hands else ""
        
        # Check if 3P mode
        is_three_player = self.combobox_players.currentText() == Dict.t("players.three")
        
        selector = TileSelector(self, mode="answer", 
                                current_selection=self.current_answer,
                                hands=hands_for_selector, answer_action=answer_action_for_selector,
                                is_three_player=is_three_player)
        selector.selection_completed.connect(self.on_answer_selected)
        selector.exec_()

    def open_dora_selector(self):
        """Call TileSelector with dora-related param"""

        hands_tiles = TileSelector.parse_tiles_string(self.current_hands) if self.current_hands else []
        
        # Check if 3P mode
        is_three_player = self.combobox_players.currentText() == Dict.t("players.three")
        
        selector = TileSelector(    self, mode="dora", 
                                    current_selection=self.current_dora,
                                    hands=self.current_hands,
                                    is_three_player=is_three_player)
        
        selector.hands_tiles = hands_tiles
        
        selector.selection_completed.connect(self.on_dora_selected)
        selector.exec_()

    def on_hands_selected(self, tiles_string):
        """After hands select"""

        self.current_hands = tiles_string
        self.hands_display.setText(tiles_string)
        self.hands_input.setText(tiles_string)

        if not tiles_string.strip() or tiles_string != self.current_hands:
            self.current_answer = ""
            self.answer_display.setText("")
            self.answer_input.setText("")
        
        self.update_select_button_state()
        self.update_answer_options_state()

    def on_hands_changed(self):
        """After hands changed"""

        current_hands = self.hands_input.text().strip()

        self.current_answer = ""
        self.answer_display.setText("")
        self.answer_input.setText("")

        self.answer_buttons.setExclusive(False)
        for btn in self.answer_buttons.buttons():
            btn.setChecked(False)
        self.answer_buttons.setExclusive(True)
        
        self.update_select_button_state()
        self.update_answer_options_state()

    def on_answer_selected(self, tiles_string):
        """After answer select"""

        self.current_answer = tiles_string
        self.answer_display.setText(tiles_string)
        self.answer_input.setText(tiles_string)

    def on_dora_selected(self, tiles_string):
        """After dora changed"""

        self.current_dora = tiles_string
        self.dora_display.setText(tiles_string)
        self.dora_input.setText(tiles_string)

    # --- Update Select button / answer option --- #
    
    def update_select_button_state(self):
        """Disable some answer choices those do not satisfy conditions"""

        has_hands = bool(self.hands_input.text().strip())
        is_skip = False
        is_furo = False
        not_selected = False

        checked_button = self.answer_buttons.checkedButton()
        if checked_button:
            answer_action = checked_button.text()
            if answer_action and (answer_action in [Dict.t("answer.skip"),
                                                    Dict.t("answer.agari"),
                                                    Dict.t("answer.ankan"),
                                                    Dict.t("answer.kan")]):
                is_skip = True
            elif (answer_action in [Dict.t("answer.chi"), 
                                    Dict.t("answer.pon"),
                                    Dict.t("answer.kan")]):
                '''is_furo = True'''

        # Disable select, it answer option not selected
        if not checked_button:
            not_selected = True
        
        self.btn_select_answer.setEnabled(has_hands and not is_skip and not not_selected)

        if is_skip or is_furo:
            self.current_answer = ""
            self.answer_display.setText("")
            self.answer_input.setText("")

    def update_answer_options_state(self):

        hands_text = self.hands_input.text().strip()
        hands_validation = self._validate_hands_format(hands_text)
        total_tiles = hands_validation["total_tiles"]
        
        discard_btn = self.answer_buttons.button(0)     # "answer.discard"
        riichi_btn = self.answer_buttons.button(1)      # "answer.riichi"
        agari_btn = self.answer_buttons.button(2)       # "answer.agari"
        ankan_btn = self.answer_buttons.button(3)       # "answer.ankan"
        skip_btn = self.answer_buttons.button(4)        # "answer.skip"
        chi_btn = self.answer_buttons.button(5)         # "answer.chi"
        pon_btn = self.answer_buttons.button(6)         # "answer.pon"
        kan_btn = self.answer_buttons.button(7)         # "answer.kan"
        
        # Check if 3 players mode is selected
        is_three_player = self.combobox_players.currentText() == Dict.t("players.three")
        
        # Rule 2: Tiles count in [0, 2, 5, 8, 11, 14], disable [Skip, Chi, Pon, Kan]
        no_foru_counts = [0, 2, 5, 8, 11, 14]
        foru_actions_enabled = total_tiles not in no_foru_counts
        skip_btn.setEnabled(foru_actions_enabled)
        chi_btn.setEnabled(foru_actions_enabled and not is_three_player)  # Disable Chi in 3-player mode
        pon_btn.setEnabled(foru_actions_enabled)
        kan_btn.setEnabled(foru_actions_enabled)
        
        # Rule 3: Tiles count in [0, 4, 7, 10, 13], disable [Discard, Riichi]
        no_discard_counts = [0, 1, 4, 7, 10, 13]
        discard_enabled = total_tiles not in no_discard_counts
        discard_btn.setEnabled(discard_enabled)
        riichi_btn.setEnabled(discard_enabled)
        
        # Initialize variables for hand validation results
        hand_result = 0
        agari_enabled = False
        riichi_enabled = False
        ankan_enabled = False
        can_chi = False
        can_pon = False
        can_kan = False
        
        # Combined validation for all hand-based rules
        if hands_validation["valid"] and hands_text:
            tiles = Validator._parse_tiles_from_string(hands_text)
            hand_result = Validator.check_mahjong_hand(tiles)
            
            # Rule 4: check_mahjong_hand must return 3 or 1 (Agari in turn or Tenpai in others turn), enable Agari
            agari_enabled = hand_result in [3, 1]
            agari_btn.setEnabled(agari_enabled)

            # Rule 5: check_mahjong_hand must return 3, 2 (Agari in turn or Tenpai in turn), enable Riichi
            riichi_enabled = hand_result in [3, 2] 
            riichi_btn.setEnabled(riichi_btn.isEnabled() and riichi_enabled)
            
            # Rule 6: have at least 1 set of 4 same tiles and correct tile count, enable Ankan
            ankan_enabled = Validator.can_ankan(hands_text)
            ankan_btn.setEnabled(ankan_enabled)
            
            # Rule 7: Check specific hand shapes for furo actions
            can_chi = Validator.can_chi(hands_text)
            can_pon = Validator.can_pon(hands_text)
            can_kan = Validator.can_kan(hands_text)
            
            # Apply Rule 7 to furo actions
            chi_btn.setEnabled(chi_btn.isEnabled() and can_chi and not is_three_player)  # Disable Chi in 3-player mode
            pon_btn.setEnabled(pon_btn.isEnabled() and can_pon)
            kan_btn.setEnabled(kan_btn.isEnabled() and can_kan)
            
            # Skip is enabled if any furo action OR agari is available
            can_skip = (can_chi or can_pon or can_kan or agari_enabled)
            skip_btn.setEnabled(skip_btn.isEnabled() and can_skip)
        
        else:
            # If hand is invalid or empty, disable all hand-dependent buttons
            agari_btn.setEnabled(False)
            riichi_btn.setEnabled(riichi_btn.isEnabled() and False)
            ankan_btn.setEnabled(False)
            chi_btn.setEnabled(chi_btn.isEnabled() and False)
            pon_btn.setEnabled(pon_btn.isEnabled() and False)
            kan_btn.setEnabled(kan_btn.isEnabled() and False)
            skip_btn.setEnabled(skip_btn.isEnabled() and False)
        
        # If disabled, clear choice
        checked_button = self.answer_buttons.checkedButton()
        if checked_button and not checked_button.isEnabled():
            self.answer_buttons.setExclusive(False)
            checked_button.setChecked(False)
            self.answer_buttons.setExclusive(True)
            self.update_select_button_state()

    # --- Image Methods --- #

    def _on_image_click(self, event):

        if event.button() == Qt.LeftButton:
            self.upload_image()

    def _on_clear_image(self):

        self.image_label.clear()
        self.image_label.setText(Dict.t("upload.hint"))
        self._apply_hint_font()
        self.btn_clear_image.setVisible(False)
        self.current_image_path = None
        self.original_pixmap = None
        self.btn_open_folder.setVisible(False)  # Hide open folder button when clearing image
        
        # Temporary files will be cleaned up on program exit.
        
        self.setFocus()

    def showEvent(self, event):
        """Called when the page becomes visible to refresh page"""
        
        super().showEvent(event)
        self.apply_font()

        self.reset_all()
    
    def resizeEvent(self, event):

        super().resizeEvent(event)
        if self.original_pixmap and not self.original_pixmap.isNull():
            self._update_image_display()
        self._position_clear_button()
    
    def _update_image_display(self):
        """Update image display based on current container size"""

        if not self.original_pixmap or self.original_pixmap.isNull():
            return
        
        container_w = self.image_label.width() - 20
        container_h = self.image_label.height() - 20
        
        img_w = self.original_pixmap.width()
        img_h = self.original_pixmap.height()
        
        scale_w = container_w / img_w if img_w > 0 else 1
        scale_h = container_h / img_h if img_h > 0 else 1
        
        scale = min(scale_w, scale_h)
        
        target_w = int(img_w * scale)
        target_h = int(img_h * scale)
        
        scaled = self.original_pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        
        self._position_clear_button()
    
    def _position_clear_button(self):
        """Put a clear button "X" on right top of the image uploader"""

        try:
            margin = 6
            # Position clear button at top-right
            self.btn_clear_image.move(self.image_label.width() - self.btn_clear_image.width() - margin, margin)
            # Position open folder button below clear button
            if self.btn_open_folder.isVisible():
                self.btn_open_folder.move(self.image_label.width() - self.btn_open_folder.width() - margin, 
                                        margin + self.btn_clear_image.height() + 5)
        except Exception:
            pass
    
    def upload_image(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self, Dict.t("upload.dialog_title"), "", "Format (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path):

        self.original_pixmap = QPixmap(file_path)
        if not self.original_pixmap.isNull():
            self._update_image_display()
            self.current_image_path = file_path
            self.btn_clear_image.setVisible(True)

            # Show open folder button if in edit mode with existing image
            if self.is_edit_mode and self.current_edit_entry_id:
                self.btn_open_folder.setVisible(True)
            # Reposition buttons after showing/hiding
            self._position_clear_button()
    
    def keyPressEvent(self, event: QKeyEvent):

        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                image = clipboard.image()
                if not image.isNull():
                    self.original_pixmap = QPixmap.fromImage(image)
                    self._update_image_display()
                    self.current_image_path = "clipboard"
                    self.btn_clear_image.setVisible(True)
                    # Don't show open folder button for clipboard images
            elif mime_data.hasUrls():
                urls = mime_data.urls()
                if urls and urls[0].isLocalFile():
                    file_path = urls[0].toLocalFile()
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        self.load_image(file_path)
        else:
            super().keyPressEvent(event)

    # --- Validation Methods (Bascially useless after using TileSelector. But still can keep) --- #

    def _validate_hands_format(self, hands_text):
        """Validate hands, can only exist 0~9 and mpsz. (Kinda useless now, coz TileSelector solves most of the problem)"""

        if not re.match(r'^[0-9mpsz]*$', hands_text):
            return {"valid": False, "error_type": "format", "total_tiles": 0}
        
        # Split hands into different parts
        parts = []
        current_part = ""
        
        for char in hands_text:
            if char in 'mpsz':
                if current_part:
                    parts.append(current_part + char)
                    current_part = ""
                else:
                    return {"valid": False, "error_type": "format", "total_tiles": 0}
            elif char in '0123456789':
                current_part += char
            else:
                return {"valid": False, "error_type": "format", "total_tiles": 0}
        
        if current_part:
            return {"valid": False, "error_type": "format", "total_tiles": 0}
        
        total_tiles = 0
        all_numbers = []
        
        for part in parts:
            suit = part[-1]
            numbers = part[:-1]
            
            if suit == 'z':
                for num in numbers:
                    if num in '089':
                        return {"valid": False, "error_type": "honor", "total_tiles": 0}
                    if not '1' <= num <= '7':
                        return {"valid": False, "error_type": "format", "total_tiles": 0}
            
            counter = Counter(numbers)
            for num, count in counter.items():
                if count > 4:
                    return {"valid": False, "error_type": "duplicate", "total_tiles": 0}
            
            total_tiles += len(numbers)
            all_numbers.extend(numbers)
        
        valid_counts = [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]
        if total_tiles not in valid_counts:
            return {"valid": False, "error_type": "count", "total_tiles": total_tiles}
        
        suit_counter = Counter([part[-1] for part in parts])
        
        duplicate_suits = [suit for suit, count in suit_counter.items() if count > 1]
        
        if duplicate_suits:
            for suit, count in suit_counter.items():
                if count > 2:
                    return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
                
            if total_tiles not in [2, 5, 8, 11, 14]:
                return {"valid": False, "error_type": "drawError", "total_tiles": total_tiles}
            
            if len(duplicate_suits) > 1:
                return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
            
            duplicate_suit = duplicate_suits[0]
            duplicate_parts = [part for part in parts if part[-1] == duplicate_suit]
            
            if parts[-1][-1] != duplicate_suit:
                return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
            
            last_part = parts[-1]
            if len(last_part) != 2:
                return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
        
        return {"valid": True, "error_type": "", "total_tiles": total_tiles}

    def _validate_answer_format(self, answer_text):

        import re
        
        if len(answer_text) != 2:
            return False
        
        if not re.match(r'^[0-9][mpsz]$', answer_text):
            return False
        
        if answer_text[1] == 'z':
            if answer_text[0] in '089':
                return False
            if not '1' <= answer_text[0] <= '7':
                return False
        
        return True

    def _validate_answer_inputs(self, answer_action, answer_input, hands_text):

        if answer_action == Dict.t("answer.skip"):
            if answer_input.strip():
                return False, "msg.warn.skipError"
            return True, ""
        
        if (not (answer_action in [Dict.t("answer.skip"),
                                Dict.t("answer.agari"),
                                Dict.t("answer.ankan"),
                                Dict.t("answer.kan")])) and not answer_input.strip():
            return False, "msg.warn.answerNoInput"
        
        '''if not self._validate_answer_format(answer_input):
            return False, "msg.warn.answerStruc"'''
    
        '''if not self._validate_answer_tiles_in_hands([answer_input], hands_text):
            return False, "msg.warn.answerDuplicate"'''
        
        return True, ""
    
    def _validate_answer_tiles_in_hands(self, answer_tiles, hands_text):

        hands_tile_counter = Counter()
        
        current_numbers = ""
        for char in hands_text:
            if char in 'mpsz':
                if current_numbers:
                    for num in current_numbers:
                        tile = num + char
                        hands_tile_counter[tile] += 1
                    current_numbers = ""
            elif char in '0123456789':
                current_numbers += char
        
        answer_tile_counter = Counter(answer_tiles)
        
        for tile, answer_count in answer_tile_counter.items():
            if tile not in hands_tile_counter:
                return False
        
        if len(answer_tiles) != len(set(answer_tiles)):
            return False
        
        return True
    
    def _validate_three_player_rules(self, players_choice, tiles_text):

        if players_choice == Dict.t("players.three") and tiles_text:
            current_numbers = ""
            for char in tiles_text:
                if char in 'mpsz':
                    if current_numbers and char == 'm':
                        for num in current_numbers:
                            if num in '2345678':
                                return False, "msg.warn.threeNoM"
                    current_numbers = ""
                elif char in '0123456789':
                    current_numbers += char
        
        return True, ""

    def _validate_meld_conditions(self, answer_action, hands_count, players_choice):
        
        meld_answers = [
            Dict.t("answer.chi"),
            Dict.t("answer.pon"), 
            Dict.t("answer.kan"),
            Dict.t("answer.skip")
        ]
        
        no_meld_counts = [2, 5, 8, 11, 14]
        
        if (answer_action in meld_answers and 
            hands_count in no_meld_counts):
            return False, "msg.warn.noNaki"
        
        if (answer_action == Dict.t("answer.chi") and 
            players_choice == Dict.t("players.three")):
            return False, "msg.warn.threeNoChi"
        
        return True, ""
    
    # --- Save Method --- #

    def save_data(self):
        """Save the data on upload page. Call DataManager save to data.json"""

        # 1. Title, 2. Source, 3. Players, 4. Info, 5. Dora, 6. Hands, 7. Answer, 
        # 8. Notes, 9. Image
        
        # 1. Title validation
        if not self.title_input.text().strip():
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.title")).exec_()
            return

        # 2. Source validation
        if self.combobox_source.currentIndex() == 0:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.platform")).exec_()
            return
        
        # 3. Players validation
        if self.combobox_players.currentIndex() == 0:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.type")).exec_()
            return
        
        # 4. Info validation
        # 4.1. No Honba
        honba_text = self.input_honba.text().strip()
        if not honba_text:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.honba")).exec_()
            return
        try:
            honba_value = int(honba_text)
            if honba_value < 0 or honba_value > 99:
                StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.honba")).exec_()
                return
        except ValueError:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.honba")).exec_()
            return
        
        # 4.2. No Turn
        turn_text = self.input_turn.text().strip()
        if not turn_text:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.turn")).exec_()
            return
        try:
            turn_value = int(turn_text)
            if turn_value < 1 or turn_value > 99:
                StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.turn")).exec_()
                return
        except ValueError:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.turn")).exec_()
            return

        # 5. Dora validation
        if not self.dora_input.text().strip():
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.doraNoInput")).exec_()
            return

        # 6. Hands validation
        # 6.1. No hand input
        if not self.hands_input.text().strip():
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.handNoInput")).exec_()
            return
        
        # 6.2. Hand format validation
        hands_validation = self._validate_hands_format(self.hands_input.text())
        if not hands_validation["valid"]:
            error_messages = {
                "format": "msg.warn.handStruc",
                "duplicate": "msg.warn.handDuplicate", 
                "count": "msg.warn.handCountError",
                "honor": "msg.warn.handStruc",
                "drawError": "msg.warn.drawError",
            }
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t(error_messages[hands_validation["error_type"]])).exec_()
            return
        
        '''# 6.3. No image, but not full hand
        if not self.current_image_path and hands_validation["total_tiles"] != 14:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.notFull")).exec_()
            return'''
        
        # 7. Answer validation
        # 7.1. Answer action selection
        if not self.answer_buttons.checkedButton():
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.answer")).exec_()
            return
        
        # 7.2. Answer input validation
        answer_input = self.answer_input.text()
        answer_valid, answer_error = self._validate_answer_inputs(
            self.answer_buttons.checkedButton().text(), answer_input, self.hands_input.text()
        )
        if not answer_valid:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t(answer_error)).exec_()
            return
        
        # 7.3. Meld conditions validation
        players_choice = self.combobox_players.currentText()
        meld_valid, meld_error = self._validate_meld_conditions(
            self.answer_buttons.checkedButton().text(), hands_validation["total_tiles"], players_choice
        )
        if not meld_valid:
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t(meld_error)).exec_()
            return
        
        # 7.4. 3P rules validation
        if players_choice == Dict.t("players.three"):
            hands_valid, hands_error = self._validate_three_player_rules(players_choice, self.hands_input.text())
            if not hands_valid:
                StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t(hands_error)).exec_()
                return
            
            dora_valid, dora_error = self._validate_three_player_rules(players_choice, self.dora_input.text())
            if not dora_valid:
                StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t(dora_error)).exec_()
                return

            if self.combobox_game.currentText() == "4":
                StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.threeNoFour")).exec_()
                return
            
            if self.combobox_wind.currentText() == Dict.t("info.north") or self.combobox_swind.currentText() == Dict.t("info.north"):
                StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.threeNoNorth")).exec_()
                return

        # 8. Intro validation
        if not self.intro_input.toPlainText().strip():
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.intro")).exec_()
            return
        
        # 9. Notes validation
        if not self.notes_input.toPlainText().strip():
            StyledMessageBox.warning(self, Dict.t("msg.hint"), Dict.t("msg.warn.notes")).exec_()
            return
        
        # All validations passed, prepare data
        
        # Get translation keys back to original format for saving
        source_index = self.combobox_source.currentIndex()
        source_keys = ["source.mahjong_soul", "source.tenhou", "source.riichi_city", "source.exercises", "source.others"]
        source_value = source_keys[source_index - 1] if source_index > 0 else ""

        players_index = self.combobox_players.currentIndex()
        players_keys = ["players.four", "players.three", "players.other"]
        players_value = players_keys[players_index - 1] if players_index > 0 else ""

        answer_id = self.answer_buttons.checkedId()
        answer_keys = ["answer.discard", "answer.riichi", "answer.agari", "answer.ankan", "answer.skip", "answer.chi", "answer.pon", "answer.kan"]
        answer_value = answer_keys[answer_id] if 0 <= answer_id < len(answer_keys) else "answer.discard"

        wind_index = self.combobox_wind.currentIndex()
        wind_keys = ["info.east", "info.south", "info.west", "info.north"]
        wind_value = wind_keys[wind_index] if 0 <= wind_index < len(wind_keys) else "info.east"

        swind_index = self.combobox_swind.currentIndex()
        swind_keys = ["info.east", "info.south", "info.west", "info.north"]
        swind_value = swind_keys[swind_index] if 0 <= swind_index < len(swind_keys) else "info.east"
        
        # Get create time from datetime picker
        create_time_dt = self.create_time_input.dateTime().toPyDateTime()
        
        # Prepare data with raw values
        if self.is_edit_mode:
            # In edit mode, preserve original data and update career stats
            data = {
                'create_time': create_time_dt.isoformat(), 'title': self.title_input.text(),
                'encounter': int(self.encounter_input.text()), 'correct': int(self.correct_input.text()), 'accuracy': self.accuracy_input.text(),
                'source': source_value, 'players': players_value, 'difficulty': int(self.difficulty_slider.value()),
                'wind': wind_value, 'self_wind': swind_value, 'game': self.combobox_game.currentText(), 'honba': honba_text, 'turn': turn_text,
                'dora': self.dora_input.text(), 'hands': self.hands_input.text(), 'answer_action': answer_value, 'answer_input': self.answer_input.text(),
                'intro': self.intro_input.toPlainText(), 'notes': self.notes_input.toPlainText()
            }
        else:
            # In normal mode, create new entry with create time from input
            data = {
                'create_time': create_time_dt.isoformat(), 'title': self.title_input.text(),
                'encounter': 0, 'correct': 0, 'accuracy': "N/A %",
                'source': source_value, 'players': players_value, 'difficulty': int(self.difficulty_slider.value()),
                'wind': wind_value, 'self_wind': swind_value, 'game': self.combobox_game.currentText(), 'honba': honba_text, 'turn': turn_text,
                'dora': self.dora_input.text(), 'hands': self.hands_input.text(), 'answer_action': answer_value, 'answer_input': self.answer_input.text(),
                'intro': self.intro_input.toPlainText(), 'notes': self.notes_input.toPlainText()
            }
        
        # Process image path
        image_path = None
        if self.current_image_path and self.current_image_path != "clipboard":
            image_path = self.current_image_path
        elif self.current_image_path == "clipboard" and self.original_pixmap:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            self.original_pixmap.save(temp_file.name, 'PNG')
            image_path = temp_file.name
            # Close the file handle immediately to avoid "file in use" errors
            temp_file.close()
            # Track only the file path for cleanup, not the file object
            self.temp_files.append(temp_file.name)
        
        # Save to database
        if self.is_edit_mode:
            # Update existing entry
            success = self.data_manager.update_entry(self.current_edit_entry_id, image_path, data)
            if success:
                StyledMessageBox.information(self, Dict.t("msg.success"), Dict.t("msg.success.save")).exec_()
                self.edit_mode_saved.emit()
                # Note: Temporary files will be cleaned up on program exit
            else:
                StyledMessageBox.critical(self, Dict.t("msg.failed"), Dict.t("msg.failed.save")).exec_()
        else:
            # Create new entry
            success = self.data_manager.save_entry(image_path, data)
            if success:
                StyledMessageBox.information(self, Dict.t("msg.success"), Dict.t("msg.success.save")).exec_()
                self.upload_complete.emit()
                # Note: Temporary files will be cleaned up on program exit
                self.clear_form()
            else:
                StyledMessageBox.critical(self, Dict.t("msg.failed"), Dict.t("msg.failed.save")).exec_()

    def clear_form(self):
        """Reset the form to default"""
        
        # Clear image
        self.image_label.clear()
        self.image_label.setText(Dict.t("upload.hint"))
        self._apply_hint_font()
        self.current_image_path = None
        self.original_pixmap = None
        self.btn_clear_image.setVisible(False)
        self.setFocus()
        
        # Clear selections
        self.combobox_source.setCurrentIndex(0)
        self.combobox_players.setCurrentIndex(0)
        
        self.answer_buttons.setExclusive(False)
        for btn in self.answer_buttons.buttons():
            btn.setChecked(False)
        self.answer_buttons.setExclusive(True)
        
        self.difficulty_slider.setValue(0)
        
        # Clear title, notes, and intro input
        self.title_input.clear()
        self.notes_input.clear()
        self.intro_input.clear()
        
        # Reset create time to current time
        self.create_time_input.setDateTime(QDateTime.currentDateTime())
        
        # Clear hands, answers, dora
        self.hands_display.setText("")
        self.current_hands = ""
        self.hands_input.setText("")
        
        self.answer_display.setText("")
        self.current_answer = ""
        self.answer_input.setText("")

        self.dora_display.setText("")
        self.current_dora = ""
        self.dora_input.setText("")

        self.update_select_button_state()
        self.update_answer_options_state()

        # Clear / reset game info
        self.combobox_wind.setCurrentIndex(0)
        self.combobox_game.setCurrentIndex(0)
        self.combobox_swind.setCurrentIndex(0)
        self.input_honba.clear()
        self.input_turn.clear()

    def reset_all(self):
        """Caller for both edit mode or upload mode"""
        
        if self.is_edit_mode:
            # In edit mode, reset to original data
            self.load_entry_data()
        else:
            # In normal mode, clear form
            self.clear_form()
    
    # --- Edit Mode Methods --- #
    
    def start_edit_mode(self, entry_id):
        """Start editing an entry"""

        self.is_edit_mode = True
        self.current_edit_entry_id = entry_id
        
        # Load entry data
        self.original_entry_data = self.data_manager.load_entry(entry_id)
        if not self.original_entry_data:
            return
        
        # Load data into form
        self.load_entry_data()
        
        # Show career stats and edit buttons
        self.career_group.setVisible(True)
        self.btn_reset_career.setVisible(True)
        self.btn_cancel.setVisible(True)
        
        # Update button texts for edit mode
        self.btn_reset.setText(Dict.t("career.edit.reset"))
        self.btn_save.setText(Dict.t("career.edit.save"))
        
        self.update_career_display()
    
    def exit_edit_mode(self):
        """Exit edit mode"""

        self.is_edit_mode = False
        self.current_edit_entry_id = None
        self.original_entry_data = None
        
        # Hide career stats and edit buttons
        self.career_group.setVisible(False)
        self.btn_reset_career.setVisible(False)
        self.btn_cancel.setVisible(False)
        
        # Update button texts for normal mode
        self.btn_reset.setText(Dict.t("action.reset"))
        self.btn_save.setText(Dict.t("action.save"))
        
        # Hide open folder button
        self.btn_open_folder.setVisible(False)
        
        self.clear_form()
    
    def load_entry_data(self):
        """Load entry data into the form (for edit mode)"""

        if not self.original_entry_data:
            return
        
        data = self.original_entry_data
        
        # Basic info
        self.title_input.setText(data.get('title', ''))
        self.intro_input.setPlainText(data.get('intro', ''))
        self.notes_input.setPlainText(data.get('notes', ''))
        
        # Create time
        create_time_str = data.get('create_time', datetime.now().isoformat())
        try:
            # Handle different datetime formats
            if create_time_str.endswith('Z'):
                create_time_str = create_time_str.replace('Z', '+00:00')
            create_time_dt = datetime.fromisoformat(create_time_str)
            self.create_time_input.setDateTime(QDateTime.fromSecsSinceEpoch(int(create_time_dt.timestamp())))
        except:
            # Fallback to current time if parsing fails
            self.create_time_input.setDateTime(QDateTime.currentDateTime())
        
        # Source and players
        source_value = data.get('source', '')
        for i in range(self.combobox_source.count()):
            if self.combobox_source.itemText(i) == Dict.t(source_value):
                self.combobox_source.setCurrentIndex(i)
                break
        
        players_value = data.get('players', '')
        for i in range(self.combobox_players.count()):
            if self.combobox_players.itemText(i) == Dict.t(players_value):
                self.combobox_players.setCurrentIndex(i)
                break
        
        # Difficulty
        self.difficulty_slider.setValue(data.get('difficulty', 0))
        
        # Game info
        wind_value = data.get('wind', 'info.east')
        for i in range(self.combobox_wind.count()):
            if self.combobox_wind.itemText(i) == Dict.t(wind_value):
                self.combobox_wind.setCurrentIndex(i)
                break
        
        self.combobox_game.setCurrentText(data.get('game', '1'))
        self.input_honba.setText(data.get('honba', ''))

        swind_value = data.get('self_wind', 'info.east')
        for i in range(self.combobox_swind.count()):
            if self.combobox_swind.itemText(i) == Dict.t(swind_value):
                self.combobox_swind.setCurrentIndex(i)
                break

        self.input_turn.setText(data.get('turn', ''))
        
        # Hands, answer, dora
        self.current_hands = data.get('hands', '')
        self.hands_display.setText(self.current_hands)
        self.hands_input.setText(self.current_hands)
        
        self.current_dora = data.get('dora', '')
        self.dora_display.setText(self.current_dora)
        self.dora_input.setText(self.current_dora)
        
        self.current_answer = data.get('answer_input', '')
        self.answer_display.setText(self.current_answer)
        self.answer_input.setText(self.current_answer)
        
        # Answer action
        answer_action = data.get('answer_action', 'answer.discard')
        answer_keys = ["answer.discard", "answer.riichi", "answer.agari", "answer.ankan", "answer.skip", "answer.chi", "answer.pon", "answer.kan"]
        if answer_action in answer_keys:
            index = answer_keys.index(answer_action)
            self.answer_buttons.button(index).setChecked(True)
        
        # Career stats
        self.encounter_input.setText(str(data.get('encounter', 0)))
        self.correct_input.setText(str(data.get('correct', 0)))
        
        accuracy = data.get('accuracy', 'N/A %')
        if accuracy == 'N/A %':
            encounter = data.get('encounter', 0)
            correct = data.get('correct', 0)
            if encounter > 0:
                accuracy = f"{(correct / encounter * 100):.1f}%"
        self.accuracy_input.setText(accuracy)
        
        # Image
        image_path = self.data_manager.get_image_path(self.current_edit_entry_id)
        if image_path and os.path.exists(image_path):
            self.load_image(image_path)
            # Show open folder button for existing images in edit mode
            self.btn_open_folder.setVisible(True)
        else:
            # Hide open folder button if no existing image
            self.btn_open_folder.setVisible(False)
        
        # Reposition buttons after showing/hiding
        self._position_clear_button()
        
        self.update_select_button_state()
        self.update_answer_options_state()
        self.update_career_display()
    
    def update_career_display(self):
        """Update career stats display based on settings"""

        from src.utils.settings_manager import SettingsManager
        settings_manager = SettingsManager()
        career_enabled = settings_manager.get("career_stats", True)
        
        if career_enabled:
            style = "color: #000000; background-color: #f0f0f0;"
            title = Dict.t("career.title.enabled")
        else:
            style = "color: #888888; background-color: #f0f0f0;"
            title = Dict.t("career.title.disabled")
            
        self.encounter_input.setStyleSheet(style)
        self.correct_input.setStyleSheet(style)
        self.accuracy_input.setStyleSheet(style)
        self.career_group.setTitle(title)
        
        # Update label colors
        for label in self.career_group.findChildren(QLabel):
            if career_enabled:
                label.setStyleSheet("color: #000000;")
            else:
                label.setStyleSheet("color: #888888;")
    
    def reset_career(self):
        """Reset career stats to 0"""

        self.encounter_input.setText("0")
        self.correct_input.setText("0")
        self.accuracy_input.setText("N/A %")
    
    def cancel_edit(self):
        """Cancel editing and exit edit mode"""

        self.edit_mode_cancelled.emit()
    
    # --- Show special help box --- #

    def show_hands_help(self):

        StyledMessageBox.information(self, Dict.t("hands.help.title"), Dict.t("hands.help.content")).exec_()
    
    def show_answer_help(self):

        StyledMessageBox.information(self, Dict.t("answer.help.title"), Dict.t("answer.help.content")).exec_()

    def show_dora_help(self):

        StyledMessageBox.information(self, Dict.t("dora.help.title"), Dict.t("dora.help.content")).exec_()

    def show_difficulty_help(self):

        StyledMessageBox.information(self, Dict.t("difficulty.help.title"), Dict.t("difficulty.help.content")).exec_()
    
    # --- UI Update Methods --- #

    def apply_font(self):
        
        widgets = [
        self.btn_reset, self.btn_save, self.btn_reset_career, self.btn_cancel,
        self.title_input, self.intro_input, self.notes_input, self.image_label,
        self.btn_select_hands, self.btn_select_answer, self.btn_select_dora,
        self.hands_display, self.answer_display, self.dora_display,
        self.encounter_input, self.correct_input, self.accuracy_input,
        self.create_time_input
        ]
        
        apply_font_to_widgets(widgets)

    def _apply_hint_font(self):
        
        from src.utils.format_applier import get_app_font
        font = get_app_font()
        self.image_label.setFont(font)
    
    def cleanup_temp_files(self):
        """Clean up temporary files created from clipboard images"""

        for temp_file_path in self.temp_files:
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except Exception as e:
                print(f"Failed to cleanup temp file: {e}")
        self.temp_files.clear()
    
    def on_players_changed(self, players_text):
        """Handle players selection change - clear tile-related fields (becoz needs disable chi / 2~8m in 3P)"""

        # Clear dora, hands, answer choice and answer input, when [players] change
        self.dora_input.clear()
        self.hands_input.clear()
        
        # Clear dora and hands display labels
        self.dora_display.setText("")
        self.hands_display.setText("")
        
        # Clear current selections
        self.current_dora = ""
        self.current_hands = ""
        self.current_answer = ""
        
        # Clear answer display and input
        self.answer_display.setText("")
        self.answer_input.clear()
        
        # Clear answer buttons
        self.answer_buttons.setExclusive(False)
        for btn in self.answer_buttons.buttons():
            btn.setChecked(False)
        self.answer_buttons.setExclusive(True)
        
        # Update button states
        self.update_select_button_state()
        self.update_answer_options_state()
    
    def _on_open_folder(self):
        """Open folder, and locate the file"""

        if self.is_edit_mode and self.current_edit_entry_id:
            image_path = self.data_manager.get_image_path(self.current_edit_entry_id)
            if image_path and os.path.exists(image_path):
                # Open folder and select the file
                import subprocess
                import platform
                
                folder_path = os.path.dirname(image_path)
                file_name = os.path.basename(image_path)
                
                try:
                    if platform.system() == "Windows":
                        # Windows: use explorer with /select parameter
                        subprocess.run(['explorer', '/select,', image_path])
                    elif platform.system() == "Darwin":  # macOS
                        # macOS: use open with -R to reveal in Finder
                        subprocess.run(['open', '-R', image_path])
                    else:  # Linux
                        # Linux: try different file managers (Really dun know)
                        subprocess.run(['xdg-open', folder_path])
                except Exception as e:
                    print(f"Failed to open folder: {e}")