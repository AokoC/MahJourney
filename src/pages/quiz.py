import random
import os
from PyQt5.QtWidgets import (   QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QFrame, QScrollArea, QMessageBox, QApplication,
                                QGraphicsOpacityEffect, QGridLayout, QButtonGroup,
                                QSizePolicy, QSpacerItem, QRadioButton, QComboBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPen, QColor

from src.utils.i18n import Dict
from src.utils.format_applier import apply_font_to_widgets
from src.utils.data_manager import DataManager
from src.utils.settings_manager import SettingsManager
from src.utils.validators import Validator

from src.widgets.entry_filter import EntryFilterDialog
from src.widgets.hint_dialog import StyledMessageBox
from src.widgets.tile_selector import TileSelector

class QuizPage(QWidget):
    """Quiz page implementation"""
    
    quiz_started = pyqtSignal()
    quiz_ended = pyqtSignal()
    
    def __init__(self, data_manager: DataManager, settings_manager: SettingsManager, parent=None):

        super().__init__(parent)
        self.data_manager = data_manager
        self.settings = settings_manager
        
        # Quiz state
        self.is_quiz_active = False
        self.current_question_index = 0  # Index in the question queue
        self.total_question_count = 0    # Accumulative question number for display
        self.question_queue = []
        self.current_entry = None
        self.selected_answer = None
        self.selected_tile = None
        self.show_notes = False
        self.tiles_enabled = True  # Track if tiles are enabled
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.time_remaining = 25
        
        # Filter state
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
        self.is_filtering = False  # Track if filter is active
        
        self.init_ui()
        
        # Initialize filter button style
        self.update_filter_button_style()
    
    def init_ui(self):
        """Initialize the UI"""

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create the initial layout (Filter and Start Quiz buttons)
        self.create_initial_layout()

        self.setLayout(self.main_layout)
    
    # --- Initial Quiz page's buttons and methods --- #

    def create_initial_layout(self):
        """Create the initial layout with two columns: left (settings) and right (start quiz)"""

        # Clear existing layout
        self.clear_layout()
        
        # Main container with two columns
        container = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)
        
        # Left column - Settings and Filter
        left_column = QVBoxLayout()
        left_column.setAlignment(Qt.AlignCenter)
        left_column.setSpacing(20)
        
        # Filter section
        filter_section = QVBoxLayout()
        filter_section.setAlignment(Qt.AlignCenter)
        filter_section.setSpacing(10)
        
        # Filter button
        self.filter_btn = QPushButton(Dict.t("quiz.filter"))
        self.filter_btn.setStyleSheet("padding: 16px;")
        self.filter_btn.clicked.connect(self.open_filter_dialog)
        filter_section.addWidget(self.filter_btn)
        
        # Queue count label
        self.queue_count_label = QLabel()
        self.queue_count_label.setStyleSheet("")
        self.queue_count_label.setAlignment(Qt.AlignCenter)
        filter_section.addWidget(self.queue_count_label)
        
        left_column.addLayout(filter_section)
        
        # Settings status section
        settings_section = QVBoxLayout()
        settings_section.setAlignment(Qt.AlignCenter)
        settings_section.setSpacing(8)
        
        # Create settings status labels
        self.create_settings_status_labels(settings_section)
        
        left_column.addLayout(settings_section)
        
        # Right column - Start Quiz button
        right_column = QVBoxLayout()
        right_column.setAlignment(Qt.AlignCenter)
        
        # Start Quiz button
        self.start_btn = QPushButton(Dict.t("quiz.start"))
        self.start_btn.setStyleSheet("padding: 48px;")
        self.start_btn.clicked.connect(self.start_quiz)
        right_column.addWidget(self.start_btn, 0, Qt.AlignCenter)
        
        # Add columns to main layout
        main_layout.addLayout(left_column, 1)
        main_layout.addLayout(right_column, 1)
        
        container.setLayout(main_layout)
        self.main_layout.addWidget(container)
        
        # Update queue count and button state
        self.update_queue_count_and_button_state()
    
    def create_settings_status_labels(self, parent_layout):
        """Create settings status labels showing current settings"""
        
        # Career Stats setting
        career_stats_enabled = self.settings.get("career_stats", True)
        career_status_text = Dict.t('quiz.enabled' if career_stats_enabled else 'quiz.disabled')
        career_status_color = "#cccccc" if not career_stats_enabled else "#000000"
        self.career_label = QLabel(f"{Dict.t('settings.career_stats')} {career_status_text}")
        self.career_label.setAlignment(Qt.AlignCenter)
        self.career_label.setStyleSheet(f"color: {career_status_color};")
        parent_layout.addWidget(self.career_label)
        
        # Timer setting
        timer_enabled = self.settings.get("timer", False)
        timer_status_text = Dict.t('quiz.enabled' if timer_enabled else 'quiz.disabled')
        timer_status_color = "#cccccc" if not timer_enabled else "#000000"
        self.timer_label = QLabel(f"{Dict.t('settings.timer')} {timer_status_text}")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(f"color: {timer_status_color};")
        parent_layout.addWidget(self.timer_label)
        
        # Endless mode setting
        endless_enabled = self.settings.get("endless", False)
        endless_status_text = Dict.t('quiz.enabled' if endless_enabled else 'quiz.disabled')
        endless_status_color = "#cccccc" if not endless_enabled else "#000000"
        self.endless_label = QLabel(f"{Dict.t('settings.endless')} {endless_status_text}")
        self.endless_label.setAlignment(Qt.AlignCenter)
        self.endless_label.setStyleSheet(f"color: {endless_status_color};")
        parent_layout.addWidget(self.endless_label)
        
    def update_settings_status_labels(self):
        """Update the settings status labels with current settings"""

        # Check if in quiz mode
        if self.is_quiz_active:
            return
            
        # Check if labels exist and haven't been deleted
        try:
            if hasattr(self, 'career_label') and self.career_label and not self.career_label.isHidden():
                career_stats_enabled = self.settings.get("career_stats", True)
                career_status_text = Dict.t('quiz.enabled' if career_stats_enabled else 'quiz.disabled')
                career_status_color = "#cccccc" if not career_stats_enabled else "#000000"
                self.career_label.setText(f"{Dict.t('settings.career_stats')} {career_status_text}")
                self.career_label.setStyleSheet(f"color: {career_status_color};")
        except RuntimeError:
            # Widget has been deleted, ignore
            pass
        
        try:
            if hasattr(self, 'timer_label') and self.timer_label and not self.timer_label.isHidden():
                timer_enabled = self.settings.get("timer", False)
                timer_status_text = Dict.t('quiz.enabled' if timer_enabled else 'quiz.disabled')
                timer_status_color = "#cccccc" if not timer_enabled else "#000000"
                self.timer_label.setText(f"{Dict.t('settings.timer')} {timer_status_text}")
                self.timer_label.setStyleSheet(f"color: {timer_status_color};")
        except RuntimeError:
            # Widget has been deleted
            pass
        
        try:
            if hasattr(self, 'endless_label') and self.endless_label and not self.endless_label.isHidden():
                endless_enabled = self.settings.get("endless", False)
                endless_status_text = Dict.t('quiz.enabled' if endless_enabled else 'quiz.disabled')
                endless_status_color = "#cccccc" if not endless_enabled else "#000000"
                self.endless_label.setText(f"{Dict.t('settings.endless')} {endless_status_text}")
                self.endless_label.setStyleSheet(f"color: {endless_status_color};")
        except RuntimeError:
            # Widget has been deleted
            pass
    
    def create_quiz_layout(self):
        """Create the quiz layout with question display"""

        self.clear_layout()
        
        # Create the basic quiz structure
        self.create_quiz_layout_structure()
        
        # Initialize quiz display
        self.display_question()
        
        self.apply_font()
    
    def clear_layout(self):
        """Clear all widgets from the main layout"""

        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout_recursive(child.layout())
    
    def clear_layout_recursive(self, layout):
        """Recursively clear a layout"""

        if layout is None:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout_recursive(child.layout())
    
    def open_filter_dialog(self):
        """Open the filter dialog"""

        dialog = EntryFilterDialog(self)
        dialog.set_filter_state(self.filter_state)
        
        if dialog.exec_() == EntryFilterDialog.Accepted:
            self.filter_state = dialog.get_filter_state()
            self.is_filtering = any([
                bool(self.filter_state['text_contains']['text'] and self.filter_state['text_contains']['fields']),
                bool(self.filter_state['text_excludes']['text'] and self.filter_state['text_excludes']['fields']),
                bool(self.filter_state['source']),
                bool(self.filter_state['players']),
                bool(self.filter_state['image']),
                (self.filter_state['difficulty_min'] > 0 or self.filter_state['difficulty_max'] < 100),
                bool(self.filter_state['wind']),
                bool(self.filter_state['self_wind']),
                bool(self.filter_state['game']),
                (self.filter_state['accuracy_min'] > 0 or self.filter_state['accuracy_max'] < 100),
                self.filter_state['start_date'] is not None,
                self.filter_state['end_date'] is not None
            ])
            self.update_filter_button_style()
            self.update_queue_count_and_button_state()
    
    def update_filter_button_style(self):
        """Update filter button style based on filter state"""
        
        if self.is_filtering:
            self.filter_btn.setStyleSheet("""
                QPushButton {
                    padding: 15px;
                    background-color: #e0eef9;
                    border: 3px solid #0078d4;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #e0eef9;
                }
            """)
        else:
            self.filter_btn.setStyleSheet("padding: 16px;")
    
    def update_queue_count_and_button_state(self):
        """Update queue count display (total count) and start button state (enabled / disabled)"""
        
        # If deleted return
        if not hasattr(self, 'queue_count_label') or self.queue_count_label is None:
            return
        if not hasattr(self, 'start_btn') or self.start_btn is None:
            return
        
        # Calculate current queue size
        queue_size = self.calculate_queue_size()
        
        # Update queue count label
        self.queue_count_label.setText("\n"+Dict.t("quiz.queue.total").format(queue_size))
        
        # Update start button state
        self.start_btn.setEnabled(queue_size > 0)
    
    def calculate_queue_size(self):
        """Calculate the size of the current question queue based on filter"""

        all_entries = self.data_manager.load_all_data()
        filtered_count = 0
        first_entry_id = None
        
        for entry_id, entry_data in all_entries.items():
            if self.matches_filter(entry_data):
                if first_entry_id is None:
                    first_entry_id = entry_id  # First entry ID debug
                filtered_count += 1
        
        # Print debug info when queue is updated
        if first_entry_id:
            print(f"Queue updated: {filtered_count} entries, first entry ID: {first_entry_id}")
        else:
            print(f"Queue updated: {filtered_count} entries (empty queue)")
        
        return filtered_count
    
    # --- Start Quiz --- #
    
    def start_quiz(self):
        """Start the quiz"""

        # Generate question queue based on filter
        self.generate_question_queue()
        
        if not self.question_queue:
            StyledMessageBox.information(self, Dict.t("msg.hint"), Dict.t("quiz.no_questions")).exec_()
            return
        
        # Start quiz
        self.is_quiz_active = True
        self.current_question_index = 0
        self.total_question_count = 1
        self.is_current_submitted = False
        self.reset_progress_stats()
        self.create_quiz_layout()
        
        # Update window title for first question
        self.update_window_title()
        
        # Emit signal
        self.quiz_started.emit()
    
    def update_window_title(self):
        """Update the main window title with current question info"""

        if self.is_quiz_active and self.current_entry:
            entry_name = self.current_entry['data'].get('title', 'Unknown')
            title = f"{Dict.t('app.title')} - {Dict.t('quiz.q').format(self.total_question_count)}{entry_name}"
            
            # Get the main window and update its title
            main_window = self.parent()
            while main_window:
                if hasattr(main_window, 'setWindowTitle') and hasattr(main_window, 'BASE_WIDTH'):
                    # This is the main window (MahJourney class)
                    main_window.setWindowTitle(title)
                    break
                main_window = main_window.parent()
    
    def reset_window_title(self):
        """Reset the main window title to the original app title"""

        main_window = self.parent()
        while main_window:
            if hasattr(main_window, 'setWindowTitle') and hasattr(main_window, 'BASE_WIDTH'):
                main_window.setWindowTitle(Dict.t('app.title'))
                break
            main_window = main_window.parent()

    def generate_question_queue(self):
        """Generate question queue based on current filter"""

        all_entries = self.data_manager.load_all_data()
        filtered_entries = []
        
        for entry_id, entry_data in all_entries.items():
            if self.matches_filter(entry_data):
                # Store both entry_id and entry_data to avoid object comparison later
                filtered_entries.append({'id': entry_id, 'data': entry_data})
        
        # Shuffle the entries
        random.shuffle(filtered_entries)
        self.question_queue = filtered_entries
    
    def refresh_quiz_data(self):
        """Refresh quiz data when page is shown (similar to library page)"""

        # Only refresh if not currently in quiz
        if not self.is_quiz_active:
            # Regenerate question queue
            self.generate_question_queue()
            # Update queue count and button state
            self.update_queue_count_and_button_state()

    def matches_filter(self, entry):
        """Same as Library's"""

        # Collects all filter applied
        filter_results = []
        
        # Include text filter
        if self.filter_state['text_contains']['text'] and self.filter_state['text_contains']['fields']:
            text_contains_match = False
            search_text = self.filter_state['text_contains']['text'].lower()
            
            for field in self.filter_state['text_contains']['fields']:
                if field == 'title':
                    if search_text in entry.get('title', '').lower():
                        text_contains_match = True
                        break
                elif field == 'intro':
                    if search_text in entry.get('intro', '').lower():
                        text_contains_match = True
                        break
                elif field == 'notes':
                    if search_text in entry.get('notes', '').lower():
                        text_contains_match = True
                        break
            
            filter_results.append(text_contains_match)
        
        # Exclude text filter
        if self.filter_state['text_excludes']['text'] and self.filter_state['text_excludes']['fields']:
            text_excludes_match = True  # Default not match, so not excluded
            search_text = self.filter_state['text_excludes']['text'].lower()
            
            for field in self.filter_state['text_excludes']['fields']:
                if field == 'title':
                    if search_text in entry.get('title', '').lower():
                        text_excludes_match = False
                        break
                elif field == 'intro':
                    if search_text in entry.get('intro', '').lower():
                        text_excludes_match = False
                        break
                elif field == 'notes':
                    if search_text in entry.get('notes', '').lower():
                        text_excludes_match = False
                        break
            
            filter_results.append(text_excludes_match)
        
        # Source filter
        if self.filter_state['source']:
            source_match = entry.get('source', '') in self.filter_state['source']
            filter_results.append(source_match)
        
        # Players filter
        if self.filter_state['players']:
            players_match = entry.get('players', '') in self.filter_state['players']
            filter_results.append(players_match)
        
        # Image filter
        if self.filter_state['image']:
            has_image = bool(entry.get('image_filename'))
            image_match = False
            if 'common.have' in self.filter_state['image'] and has_image:
                image_match = True
            if 'common.noHave' in self.filter_state['image'] and not has_image:
                image_match = True
            filter_results.append(image_match)
        
        # Wind filter
        if self.filter_state['wind']:
            wind_match = entry.get('wind', '') in self.filter_state['wind']
            filter_results.append(wind_match)
        # Self wind filter
        if self.filter_state['self_wind']:
            swind_match = entry.get('self_wind', '') in self.filter_state['self_wind']
            filter_results.append(swind_match)
        
        # Game filter
        if self.filter_state['game']:
            game_match = str(entry.get('game', '')) in self.filter_state['game']
            filter_results.append(game_match)
        
        # Difficulty filter
        if (self.filter_state['difficulty_min'] > 0 or self.filter_state['difficulty_max'] < 100):
            difficulty = int(entry.get('difficulty', 0))
            if difficulty < 0: # Changed from == 0 to < 0, since 0 should count in filter now...
                difficulty_match = False
            else:
                difficulty_match = (self.filter_state['difficulty_min'] <= difficulty <= self.filter_state['difficulty_max'])
            filter_results.append(difficulty_match)
        
        # Accuracy filter
        if (self.filter_state['accuracy_min'] > 0 or self.filter_state['accuracy_max'] < 100):
            accuracy_str = entry.get('accuracy', 'N/A %')
            if accuracy_str == 'N/A %' or not accuracy_str:
                accuracy_match = False
            else:
                try:
                    if str(accuracy_str).endswith('%'):
                        accuracy_value = float(str(accuracy_str)[:-1])
                    else:
                        accuracy_value = float(accuracy_str)

                    accuracy_match = (self.filter_state['accuracy_min'] <= accuracy_value <= self.filter_state['accuracy_max'])
                except (ValueError, TypeError):
                    accuracy_match = False
            filter_results.append(accuracy_match)
        
        # Date filter
        if self.filter_state['start_date'] or self.filter_state['end_date']:
            entry_date_str = entry.get('create_time', '')
            if entry_date_str:
                try:
                    from datetime import datetime
                    # Parse ISO format date (e.g., "2025-10-10T19:06:41.402801")

                    entry_date = datetime.fromisoformat(entry_date_str.replace('Z', '+00:00')).date()
                    date_match = True

                    if self.filter_state['start_date']:
                        start_date = self.filter_state['start_date'].date() if hasattr(self.filter_state['start_date'], 'date') else self.filter_state['start_date']
                        if entry_date < start_date:
                            date_match = False

                    if self.filter_state['end_date']:
                        end_date = self.filter_state['end_date'].date() if hasattr(self.filter_state['end_date'], 'date') else self.filter_state['end_date']
                        if entry_date > end_date:
                            date_match = False

                    filter_results.append(date_match)
                except (ValueError, AttributeError):
                    # If date parsing fails, skip this entry
                    filter_results.append(False)
            else:
                filter_results.append(False)
        
        # Return true if all defaults
        if not filter_results:
            return True
        
        # Apply and, or
        if self.filter_state['logic_mode'] == 'OR':
            result = any(filter_results)
        else:
            result = all(filter_results)
        
        # Apply not
        if self.filter_state['negate']:
            result = not result
        
        return result
    
    def display_question(self):
        """Display the current question"""

        self.selected_answer = None
        self.selected_tile = None

        # Set tiles enabled, to be clickable
        if hasattr(self, 'tile_labels'):
            self.set_tiles_enabled(True)

        if self.current_question_index >= len(self.question_queue):
            # End of queue, generate new one
            self.generate_question_queue()
            self.current_question_index = 0
        
        self.current_entry = self.question_queue[self.current_question_index]
        
        # Reset selection state
        self.selected_answer = None
        self.selected_tile = None
        
        # Clear tile labels reference
        if hasattr(self, 'tile_labels'):
            self.tile_labels.clear()
        
        # Clear answer buttons reference to prevent signal conflicts
        if hasattr(self, 'answer_buttons'):
            try:
                self.answer_buttons.buttonClicked.disconnect()
            except TypeError:
                # No connections to disconnect
                pass
        
        # Check if there is quiz_content
        if not hasattr(self, 'quiz_content') or not self.quiz_content.layout():
            self.create_quiz_layout_structure()
        else:
            self.update_quiz_content()
        
        # Start timer if enabled
        if self.settings.get("timer", False):
            self.time_remaining = 25
            self.timer.start(1000)  # Update every second
            self.update_timer()
        else:
            self.timer.stop()
            self.timer_label.hide()

        self.update_progress_display()

        # Select discard (for most of the questions)
        self.select_discard_if_only_option()

    def select_discard_if_only_option(self):
        """Automatically select discard option if it's the only available answer"""

        if not hasattr(self, 'answer_buttons'):
            return

        available_buttons = self.answer_buttons.buttons()
        if not available_buttons:
            return
        
        if len(available_buttons) == 1:
            only_button = available_buttons[0]
            if only_button.text() == Dict.t("answer.discard"):
                self.on_answer_selected(only_button)
    
    # --- Quiz's question display methods --- #

    def create_quiz_layout_structure(self):
        """Create the basic quiz layout structure (only called once)"""

        # Quit + Qx (left) and Timer + Submit (right) buttons
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 20, 20, 20)
        
        # Quit button (top left)
        self.quit_btn = QPushButton(Dict.t("quiz.quit"))
        self.quit_btn.setStyleSheet("padding: 8px")
        self.quit_btn.clicked.connect(self.quit_quiz)
        top_layout.addWidget(self.quit_btn)

        # Qx Label (top left, after quit button)
        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                color: black;
                font-weight: bold;
            }
        """)
        top_layout.addWidget(self.progress_label)
        self.correct_count = 0
        self.total_answered = 0

        # Top, add stretch
        top_layout.addStretch()

        # Result label (top right, before timer)
        self.result_label = QLabel()
        self.result_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                font-weight: bold;
            }
        """)
        self.result_label.hide()
        top_layout.addWidget(self.result_label)
        
        # Timer label (top right, before submit button)
        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                color: black;
                font-weight: bold;
            }
        """)
        top_layout.addWidget(self.timer_label)
        
        # Submit button (top right)
        self.submit_btn = QPushButton(Dict.t("quiz.submit"))
        self.submit_btn.setEnabled(False)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                padding: 7px;
                background-color: #90caf9;
                color: white;
                border: 1px solid #64b5f6;
                border-radius: 4px;
            }
            QPushButton:enabled {
                background-color: #1976d2;
                border: 1px solid #0d47a1;
            }
            QPushButton:enabled:hover {
                background-color: #1565c0;
            }
        """)
        self.submit_btn.clicked.connect(self.submit_answer)
        top_layout.addWidget(self.submit_btn)
        
        self.main_layout.addLayout(top_layout)
        
        # Main quiz content
        self.quiz_content = QWidget()
        self.main_layout.addWidget(self.quiz_content)
        
        # 2 Columns
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left column
        self.left_column = QVBoxLayout()
        self.left_column.setSpacing(15)
        
        # Right column
        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(15)
        
        # Add columns to main layout with proper stretch
        main_layout.addLayout(self.left_column, 35)
        main_layout.addLayout(self.right_column, 65)
        
        self.quiz_content.setLayout(main_layout)

    def update_quiz_content(self):
        """Update the content of existing quiz layout for new question"""

        # Clear both columns content
        self.clear_layout_recursive(self.left_column)
        self.clear_layout_recursive(self.right_column)
        
        # Rebuild
        # Left column
        self.create_dora_box(self.left_column, 10)
        self.create_source_box(self.left_column, 10)
        self.create_intro_notes_box(self.left_column, 80)
        
        # Right column
        self.create_image_box(self.right_column, 70)
        self.create_answer_choice_box(self.right_column, 10)
        self.create_hands_box(self.right_column, 20)
        
        self.update_answer_button_states()
        self.apply_font()

    def create_simple_box(self, parent_layout, title, stretch=1):
        """Create a simple box with just title as placeholder"""

        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 1px solid; }")
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(0, 0, 0, 0)
        # frame_layout.addWidget(title_label)
        frame.setLayout(frame_layout)
        
        parent_layout.addWidget(frame, stretch)

    def create_dora_box(self, parent_layout, stretch=1):
        """Create Dora display box with tiles and backs"""

        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 0px; }")
        
        # Title
        title_label = QLabel("Dora!!!??")
        title_label.setStyleSheet("font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Dora tiles layout
        dora_layout = QHBoxLayout()
        dora_layout.setAlignment(Qt.AlignCenter)
        dora_layout.setSpacing(0)
        
        # Get dora from current entry
        dora_text = self.current_entry['data'].get('dora', '') if self.current_entry else ''
        dora_tiles = self.parse_dora_tiles(dora_text)
        
        # Display dora tiles and backs
        for i in range(5):  # Maximum 5 dora tiles
            if i < len(dora_tiles):
                # Show actual dora tile
                tile_frame = QFrame()
                tile_frame.setFixedSize(45, 60)
                tile_layout = QVBoxLayout(tile_frame)
                tile_layout.setContentsMargins(0, 0, 0, 0)
                
                tile_label = QLabel()
                tile_filename = f"{dora_tiles[i]}.png"
                tile_path = os.path.join("src", "assets", "tiles", tile_filename)
                
                if os.path.exists(tile_path):
                    pixmap = QPixmap(tile_path)
                    pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    tile_label.setPixmap(pixmap)
                else:
                    # Fallback..
                    tile_label.setText(dora_tiles[i])
                    tile_label.setAlignment(Qt.AlignCenter)
                    tile_label.setStyleSheet("border: 1px solid;")
                
                tile_label.setFixedSize(45, 60)
                tile_layout.addWidget(tile_label)
                dora_layout.addWidget(tile_frame)
            else:
                # Show tile back as placeholder
                back_frame = QFrame()
                back_frame.setFixedSize(45, 60)
                back_layout = QVBoxLayout(back_frame)
                back_layout.setContentsMargins(0, 0, 0, 0)
                
                back_label = QLabel()
                back_path = os.path.join("src", "assets", "tiles", "back.png")
                
                if os.path.exists(back_path):
                    pixmap = QPixmap(back_path)
                    pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    back_label.setPixmap(pixmap)
                else:
                    # Fallback
                    back_label.setText("?")
                    back_label.setAlignment(Qt.AlignCenter)
                    back_label.setStyleSheet("border: 1px solid;")
                
                back_label.setFixedSize(45, 60)
                back_layout.addWidget(back_label)
                dora_layout.addWidget(back_frame)
        
        # Main frame layout
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(10)
        # frame_layout.addWidget(title_label)
        frame_layout.addLayout(dora_layout)
        frame.setLayout(frame_layout)
        
        parent_layout.addWidget(frame, stretch)

    def create_source_box(self, parent_layout, stretch=1):
        """Create Source display box with basic info"""

        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 0px; }")
        
        # Title
        title_label = QLabel("Source and info")
        title_label.setStyleSheet("font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Source and info layout
        source_layout = QVBoxLayout()
        
        # Get source, info from current entry
        source_text = self.current_entry['data'].get('source', '') if self.current_entry else ''
        player_text = self.current_entry['data'].get('players', '') if self.current_entry else ''
        wind_text = self.current_entry['data'].get('wind', '') if self.current_entry else ''
        game_text = self.current_entry['data'].get('game', '') if self.current_entry else ''
        honba_text = self.current_entry['data'].get('honba', '') if self.current_entry else ''
        swind_text = self.current_entry['data'].get('self_wind', '') if self.current_entry else ''
        turn_text = self.current_entry['data'].get('turn', '') if self.current_entry else ''

        # Add difficulty if > 0
        difficulty_text = ""
        if self.current_entry and self.current_entry['data'].get('difficulty', 0) > 0:
            difficulty_text = f" ★{self.current_entry['data']['difficulty']}"
        
        final_text = (  f'{Dict.t("common.openBrac")}{Dict.t(source_text)}{Dict.t("common.closeBrac")}'
                        f'{Dict.t(player_text)}{difficulty_text}\n\n'
                        f'{Dict.t(wind_text)} {game_text}{Dict.t("info.gameFor4Lang")}'
                        f'{honba_text}{Dict.t("info.honbaFor4Lang")}\n'
                        f'{Dict.t(swind_text)}{Dict.t("info.swindFor4Lang")}'
                        f'{turn_text} {Dict.t("info.turn")}')

        info_label = QLabel(final_text)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        source_layout.addWidget(info_label)

        # Main frame layout
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(10, 20, 10, 30)
        frame_layout.setSpacing(10)
        # frame_layout.addWidget(title_label)
        frame_layout.addLayout(source_layout)
        frame.setLayout(frame_layout)
        
        parent_layout.addWidget(frame, stretch)

    def create_intro_notes_box(self, parent_layout, stretch=1):
        """Create Intro display box with scrollable text, that can switch to notes after submit"""

        frame = QFrame()
        frame.setObjectName("introFrame")
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("#introFrame { border-top: 2px solid; border-bottom: 0px; border-left: 0px; border-right: 0px; }")
        
        # Create scroll area for long text
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: white; }")
        
        # Create content widget
        content_widget = QWidget()
        content_widget.setObjectName("introContentWidget")  # identifier for Notes
        content_widget.setStyleSheet("QWidget { background-color: white; }")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(50, 50, 50, 50)
        content_layout.setSpacing(5)
        
        # Title label
        title_label = QLabel(Dict.t("upload.intro") + "\n")
        title_label.setObjectName("introTitleLabel")
        title_label.setStyleSheet("font-weight: bold; padding: 0px;")
        title_label.setAlignment(Qt.AlignLeft)
        
        # Get intro text
        intro_text = self.current_entry['data'].get('intro', '') if self.current_entry else ''
        
        # Content label
        content_label = QLabel(intro_text)
        content_label.setObjectName("introContentLabel")
        content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        content_label.setWordWrap(True)
        content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(content_label)
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        
        # Main frame layout
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        frame_layout.addWidget(scroll_area)
        frame.setLayout(frame_layout)
        
        parent_layout.addWidget(frame, stretch)

    def create_image_box(self, parent_layout, stretch=1):
        """Create image display box"""

        # Check if current entry has image
        image_filename = self.current_entry['data'].get('image_filename', '') if self.current_entry else ''
        image_path = None
        
        if image_filename:
            # Use the stored entry ID directly
            entry_id = self.current_entry['id']
            image_path = self.data_manager.get_image_path(entry_id)
        
        # If no image, don't add the box at all
        if not image_filename or not image_path or not os.path.exists(image_path):
            return
        
        # Title
        title_label = QLabel("Image")
        title_label.setStyleSheet("font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 0px; background-color: white; }")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Image
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(10, 10, 10, 10)
        
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("QLabel { background-color: white; border: none; }")
        image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        image_label.setScaledContents(False)
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                image_label.original_pixmap = pixmap
                
                def resizeEvent(event):
                    if hasattr(image_label, 'original_pixmap') and image_label.original_pixmap:
                        available_size = event.size()
                        pixmap_size = image_label.original_pixmap.size()
                        
                        scale_x = available_size.width() / pixmap_size.width()
                        scale_y = available_size.height() / pixmap_size.height()
                        scale = min(scale_x, scale_y)
                        
                        new_size = pixmap_size * scale
                        scaled_pixmap = image_label.original_pixmap.scaled(
                            new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        image_label.setPixmap(scaled_pixmap)
                    
                    QLabel.resizeEvent(image_label, event)
                
                image_label.resizeEvent = resizeEvent
                image_label.setPixmap(pixmap)
        
        image_layout.addWidget(image_label)
        
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addLayout(image_layout)
        frame.setLayout(frame_layout)
        
        parent_layout.addWidget(frame, stretch)

    def create_answer_choice_box(self, parent_layout, stretch=1):
        """Create answer choice box with buttons"""

        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 0px; }")
        
        # Title
        title_label = QLabel("Answer choice")
        title_label.setStyleSheet("font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Answer choices layout
        choices_layout = QHBoxLayout()
        choices_layout.setAlignment(Qt.AlignCenter)
        choices_layout.setSpacing(10)
        
        # Create buttons for answer choices
        # Clear previous button group if exists
        if hasattr(self, 'answer_buttons'):
            try:
                self.answer_buttons.buttonClicked.disconnect()
            except TypeError:
                pass
        
        self.answer_buttons = QButtonGroup(self)
        answer_keys = [
            "answer.discard",
            "answer.riichi", 
            "answer.agari",
            "answer.ankan",
            "answer.chi",
            "answer.pon",
            "answer.kan",
            "answer.skip"
        ]
        
        # Get hands data to determine which options should be hidden
        hands_text = self.current_entry['data'].get('hands', '') if self.current_entry else ''
        hands_validation = self._validate_hands_format(hands_text) if hands_text else {"total_tiles": 0, "valid": False}
        total_tiles = hands_validation.get("total_tiles", 0)
        
        # Filter answer keys based on hands structure logic
        valid_answer_keys = []
        for i, key in enumerate(answer_keys):
            should_hide = False
            
            if key == "answer.discard" or key == "answer.riichi":
                # Rule 2: Tiles count in [0, 4, 7, 10, 13], hide [Discard, Riichi]
                no_discard_counts = [0, 1, 4, 7, 10, 13]
                should_hide = total_tiles in no_discard_counts
            
            if key in ["answer.skip", "answer.chi", "answer.pon", "answer.kan"]:
                # Rule 3: Tiles count in [0, 1, 2, 5, 8, 11, 14], hide [Skip, Chi, Pon, Kan]
                no_furo_counts = [0, 1, 2, 5, 8, 11, 14]
                should_hide = total_tiles in no_furo_counts
                
                # Rule 4: Additional validation for specific actions (only if not already hidden)
                if not should_hide and hands_validation.get("valid", False) and hands_text:
                    if key == "answer.chi":
                        should_hide = not Validator.can_chi(hands_text)
                    elif key == "answer.pon":
                        should_hide = not Validator.can_pon(hands_text)
                    elif key == "answer.kan":
                        should_hide = not Validator.can_kan(hands_text)
                
                if hands_validation.get("valid", False) and hands_text and key == "answer.skip":
                    can_chi, can_pon, can_kan = False, False, False
                    in_turn = total_tiles in [2, 5, 8, 11, 14]
                    if not in_turn:
                        can_chi = Validator.can_chi(hands_text)
                        can_pon = Validator.can_pon(hands_text)
                        can_kan = Validator.can_kan(hands_text)
                    tiles = Validator._parse_tiles_from_string(hands_text)
                    hand_result = Validator.check_mahjong_hand(tiles)
                    can_agari = hand_result in [3, 1]
                    should_hide = not (can_chi or can_pon or can_kan or (can_agari and not in_turn))
                    '''print(can_agari, in_turn, should_hide)
                    print(can_chi, can_pon, can_kan)'''
            
            if key == "answer.agari":
                # Rule for agari: check_mahjong_hand must return 3 or 1
                if hands_validation.get("valid", False) and hands_text:
                    tiles = Validator._parse_tiles_from_string(hands_text)
                    hand_result = Validator.check_mahjong_hand(tiles)
                    should_hide = hand_result not in [3, 1]
                else:
                    should_hide = True

            if key == "answer.riichi":
                # Rule for riichi: check_mahjong_hand must return 3 or 2
                if hands_validation.get("valid", False) and hands_text:
                    tiles = Validator._parse_tiles_from_string(hands_text)
                    hand_result = Validator.check_mahjong_hand(tiles)
                    should_hide = hand_result not in [3, 2]
                else:
                    should_hide = True
            
            if key == "answer.ankan":
                # Rule for ankan: must have at least 1 set of 4 same tiles and correct tile count
                if hands_validation.get("valid", False) and hands_text:
                    should_hide = not Validator.can_ankan(hands_text)
                else:
                    should_hide = True
            
            # Only create buttons for valid options
            if not should_hide:
                valid_answer_keys.append((i, key))
        
        # Create only the valid buttons
        for i, key in valid_answer_keys:
            btn = QPushButton(Dict.t(key))
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: white;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            choices_layout.addWidget(btn)
            self.answer_buttons.addButton(btn, i)
        
        # Connect button events - use lambda to avoid signal conflicts
        self.answer_buttons.buttonClicked.connect(lambda button: self.on_answer_selected(button))
        
        # Main frame layout
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(10)
        # frame_layout.addWidget(title_label)
        frame_layout.addLayout(choices_layout)
        frame.setLayout(frame_layout)
        
        parent_layout.addWidget(frame, stretch)

    def create_hands_box(self, parent_layout, stretch=1):
        """Create hands display box with clickable tiles"""

        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 0px;}")
        
        # Title
        title_label = QLabel("Hands")
        title_label.setStyleSheet("font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Hands layout
        hands_layout = QHBoxLayout()
        hands_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        hands_layout.setSpacing(5)
        
        # Get hands data from current entry
        hands_text = self.current_entry['data'].get('hands', '') if self.current_entry else ''
        
        if hands_text:
            # Initialize tile labels list for this hands box
            if not hasattr(self, 'tile_labels'):
                self.tile_labels = []
            
            # Parse hands tiles similar to library.py list mode
            tiles = self.parse_hand_tiles_for_display(hands_text)
            tile_size = 80
            
            # Apply special hand display logic
            self.display_hand_tiles_for_quiz(hands_layout, tiles, tile_size)
        
        # Main frame layout
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(10)
        # frame_layout.addWidget(title_label)
        frame_layout.addLayout(hands_layout)
        frame.setLayout(frame_layout)
        
        parent_layout.addWidget(frame, stretch)

    # --- Quiz's Question assist methods --- #

    def parse_dora_tiles(self, dora_text):
        """Parse dora text into individual tiles to show"""

        if not dora_text:
            return []
        
        tiles = []
        current_numbers = ""
        
        for char in dora_text:
            if char in 'mpsz':
                if current_numbers:
                    for num in current_numbers:
                        tiles.append(num + char)
                    current_numbers = ""
            elif char in '0123456789':
                current_numbers += char
        
        return tiles
    
    def on_answer_selected(self, button):
        """Handle answer selection - disable tiles"""

        self.selected_answer = button.text()
        
        is_skip_answer = self.selected_answer in [
            Dict.t("answer.skip"), 
            Dict.t("answer.agari"), 
            Dict.t("answer.ankan"),
            Dict.t("answer.kan")
        ]
        
        if is_skip_answer:
            self.selected_tile = None
            self.update_tile_selection_state()
            self.set_tiles_enabled(False)
        else:
            self.set_tiles_enabled(True)
        
        self.update_answer_button_states()
        self.check_submit_enabled()
    
    def set_tiles_enabled(self, enabled):
        """Enable or disable tile interaction and set transparency"""

        self.tiles_enabled = enabled 
        
        if not hasattr(self, 'tile_labels') or not self.tile_labels:
            return
        
        for tile_label in self.tile_labels[:]:
            try:
                if enabled:
                    tile_label.setCursor(Qt.PointingHandCursor)
                    effect = tile_label.graphicsEffect()
                    if effect is not None:
                        effect.setEnabled(False)
                else:
                    tile_label.setCursor(Qt.ArrowCursor)
                    from PyQt5.QtWidgets import QGraphicsOpacityEffect
                    opacity_effect = QGraphicsOpacityEffect()
                    opacity_effect.setOpacity(0.4)
                    tile_label.setGraphicsEffect(opacity_effect)
                
            except RuntimeError:
                self.tile_labels.remove(tile_label)

    def update_answer_button_states(self):
        """Update answer button visual states based on selection"""

        if not hasattr(self, 'answer_buttons'):
            return
        
        for button in self.answer_buttons.buttons():
            if button.text() == self.selected_answer:
                button.setStyleSheet("""
                    QPushButton {
                        padding: 2px 10px;
                        border: 7px solid #0056b3;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        /* background-color: #e0eef9; */
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        padding: 8px 16px;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        background-color: white;
                    }
                    QPushButton:hover {
                        /* background-color: #f0f0f0; */
                    }
                """)
            button.setCursor(Qt.PointingHandCursor)
        
        is_skip_answer = self.selected_answer in [
            Dict.t("answer.skip"), 
            Dict.t("answer.agari"), 
            Dict.t("answer.ankan"),
            Dict.t("answer.kan")
        ]
        if is_skip_answer:
            self.set_tiles_enabled(False)
        else:
            self.set_tiles_enabled(True)
    
    def on_tile_selected(self, tile_index):
        """Handle tile selection"""
        
        if not self.tiles_enabled:
            return
        
        self.selected_tile = tile_index
        self.check_submit_enabled()
    
    def _validate_hands_format(self, hands_text):
        """Validate hands format (similar to Upload)"""

        from src.utils.validators import Validator
        return Validator.validate_hands_format(hands_text)

    def parse_hand_tiles_for_display(self, hand_text):
        """Parse hand text into tile list for display (similar to Library)"""

        from src.utils.validators import Validator
        return Validator.parse_hand_tiles_for_display(hand_text)

    def create_clickable_tile_label(self, tile, tile_size, tile_index):
        """Create clickable tile label with overlay border when selected"""

        tile_label = QLabel()
        tile_filename = f"{tile}.png"
        tile_path = os.path.join("src", "assets", "tiles", tile_filename)
        
        # Set up clickable functionality
        tile_label.setCursor(Qt.PointingHandCursor)
        tile_label.tile_index = tile_index
        tile_label.tile_value = tile
        tile_label.original_pixmap = None
        
        # Set up click event
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.on_tile_selected(tile_index)
                # Update visual state
                self.update_tile_selection_state()
        
        tile_label.mousePressEvent = mousePressEvent
        
        if os.path.exists(tile_path):
            pixmap = QPixmap(tile_path)
            pixmap = pixmap.scaled(56, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            tile_label.original_pixmap = pixmap
            tile_label.setPixmap(pixmap)
        else:
            tile_label.setText(tile)
            tile_label.setAlignment(Qt.AlignCenter)
        
        tile_label.setFixedSize(56, 80)
        tile_label.setStyleSheet("border: none; background-color: transparent;")
        
        if not hasattr(self, 'tile_labels'):
            self.tile_labels = []
        self.tile_labels.append(tile_label)
        
        return tile_label

    def update_tile_selection_state(self):
        """Update tile selection visual state by modifying pixmap"""

        if not hasattr(self, 'tile_labels'):
            return
        
        for tile_label in self.tile_labels[:]:
            try:
                if hasattr(tile_label, 'tile_index') and tile_label.tile_index == self.selected_tile:
                    # Selected tile - blue border
                    if hasattr(tile_label, 'original_pixmap') and tile_label.original_pixmap:
                        # New pixmap
                        pixmap_with_border = QPixmap(tile_label.original_pixmap.size())
                        pixmap_with_border.fill(Qt.transparent)

                        painter = QPainter(pixmap_with_border)

                        painter.drawPixmap(0, 0, tile_label.original_pixmap)

                        pen = QPen(QColor("#0056B3"))
                        pen.setWidth(8)
                        painter.setPen(pen)
                        painter.setBrush(Qt.NoBrush)

                        from PyQt5.QtCore import QRectF
                        rect = pixmap_with_border.rect()
                        border_rect = QRectF(3, 3, rect.width() - 6, rect.height() - 6)
                        corner_radius = 6

                        painter.drawRoundedRect(border_rect, corner_radius, corner_radius)
                        
                        painter.end()
                        tile_label.setPixmap(pixmap_with_border)
                else:
                    # Not selected - original
                    if hasattr(tile_label, 'original_pixmap') and tile_label.original_pixmap:
                        tile_label.setPixmap(tile_label.original_pixmap)
            except RuntimeError:
                self.tile_labels.remove(tile_label)

    def display_hand_tiles_for_quiz(self, hands_layout, tiles, tile_size):
        """Display hand tiles for quiz with clickable functionality"""

        total_tiles = len(tiles)
        
        fixed_tile_width = 56
        fixed_tile_height = 80
        
        if total_tiles in [2, 5, 8, 11, 14] and total_tiles > 1:
            main_tiles = tiles[:-1]
            last_tile = tiles[-1]
            
            # Display main tiles (already sorted by parse)
            for i, tile in enumerate(main_tiles):
                tile_label = self.create_clickable_tile_label(tile, fixed_tile_height, i)
                hands_layout.addWidget(tile_label)

            # Display last tile
            spacer = QLabel()
            spacer.setFixedWidth(50)
            hands_layout.addWidget(spacer)
            last_tile_label = self.create_clickable_tile_label(last_tile, fixed_tile_height, len(tiles)-1)
            hands_layout.addWidget(last_tile_label)
        else:
            # Normal display
            for i, tile in enumerate(tiles):
                tile_label = self.create_clickable_tile_label(tile, fixed_tile_height, i)
                hands_layout.addWidget(tile_label)            

    # --- Submit and Next --- #

    def check_submit_enabled(self):
        """Check if submit button should be enabled"""
        
        has_answer = self.selected_answer is not None
        
        is_skip_answer = self.selected_answer in [
            Dict.t("answer.skip"), 
            Dict.t("answer.agari"), 
            Dict.t("answer.ankan"),
            Dict.t("answer.kan")
        ]
        has_tile_or_skip = (self.selected_tile is not None) or is_skip_answer

        self.submit_btn.setEnabled(has_answer and has_tile_or_skip)
    
    def submit_answer(self):
        """Submit the current answer"""

        if not self.submit_btn.isEnabled():
            return
        
        # Stop timer
        self.timer.stop()
        
        # Validate answer
        is_correct = self.validate_answer()

        self.update_progress_stats(is_correct)
        self.is_current_submitted = True
        self.update_progress_display()
        
        # Update career stats if enabled
        if self.settings.get("career_stats", False):
            self.update_career_stats(is_correct)
        
        # Disable all interactions
        self.disable_all_interactions()
        
        # Change intro to notes
        self.show_notes_content()
        
        # Update visual states for answer choices and hands (green / red border)
        self.update_answer_feedback()
        
        # Change submit button to next
        self.submit_btn.setText(Dict.t("quiz.next"))
        self.submit_btn.clicked.disconnect()
        self.submit_btn.clicked.connect(self.next_question)
        self.submit_btn.setEnabled(True)
    
    def disable_all_interactions(self):
        """Disable all answer choices and hand tiles interactions (without changing opacity)"""

        # Disable answer buttons
        if hasattr(self, 'answer_buttons'):
            for button in self.answer_buttons.buttons():
                button.setEnabled(False)
        
        # Disable hand tiles
        self.set_tiles_enabled(False)

    def validate_answer(self):
        """Validate the user's answer and return True if correct"""

        if not self.current_entry:
            return False
        
        # Get correct answers from entry
        correct_action = self.current_entry['data'].get('answer_action', '')
        correct_input = self.current_entry['data'].get('answer_input', '')
        
        # Case 1: Check if skip action
        is_skip_answer = self.selected_answer in [
            Dict.t("answer.skip"), 
            Dict.t("answer.agari"), 
            Dict.t("answer.ankan"),
            Dict.t("answer.kan")
        ]
        if is_skip_answer:
            if self.selected_answer == Dict.t("answer.skip"):
                return correct_action == "answer.skip"
            elif self.selected_answer == Dict.t("answer.agari"):
                return correct_action == "answer.agari"
            elif self.selected_answer == Dict.t("answer.ankan"):
                return correct_action == "answer.ankan"
            elif self.selected_answer == Dict.t("answer.kan"):
                return correct_action == "answer.kan"
        
        # Case 2: Regular answer - check both action and tile
        # Check action
        action_correct = False
        if self.selected_answer:
            # Map button text back to translation key
            for key in ["answer.discard", "answer.riichi", "answer.agari", "answer.ankan",
                        "answer.chi", "answer.pon", "answer.kan", "answer.skip"]:
                if self.selected_answer == Dict.t(key):
                    action_correct = (key == correct_action)
                    break
        
        # Check tile selection
        tile_correct = False
        if self.selected_tile is not None and hasattr(self, 'tile_labels'):
            # Get the selected tile value
            selected_tile_label = None
            for tile_label in self.tile_labels:
                if hasattr(tile_label, 'tile_index') and tile_label.tile_index == self.selected_tile:
                    selected_tile_label = tile_label
                    break
            
            if selected_tile_label and hasattr(selected_tile_label, 'tile_value'):
                selected_tile_value = selected_tile_label.tile_value
                correct_tiles = TileSelector.parse_tiles_string(correct_input)
                tile_correct = selected_tile_value in correct_tiles
        
        return action_correct and tile_correct

    def parse_answer_input_tiles(self, answer_input):
        """Parse answer input into individual tiles (...)"""

        if not answer_input:
            return []
        
        tiles = []
        i = 0
        while i < len(answer_input):
            if answer_input[i] in '0123456789':
                if i + 1 < len(answer_input) and answer_input[i + 1] in 'mpsz':
                    tiles.append(answer_input[i] + answer_input[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        
        return tiles

    def update_answer_feedback(self):
        """Update visual feedback for answer choices and hands"""

        if not self.current_entry:
            return
        
        # Get correct answers
        correct_action = self.current_entry['data'].get('answer_action', '')
        correct_input = self.current_entry['data'].get('answer_input', '')
        
        # Parse correct tiles using TileSelector's static method
        from src.widgets.tile_selector import TileSelector
        correct_tiles = TileSelector.parse_tiles_string(correct_input)
        
        # Update answer choice buttons and hand tiles
        self.update_answer_buttons_feedback(correct_action)
        self.update_hands_tiles_feedback(correct_tiles)

    def update_answer_buttons_feedback(self, correct_action):
        """Update answer buttons with correct/incorrect feedback"""

        if not hasattr(self, 'answer_buttons'):
            return
        
        # Get correct action text
        correct_action_text = Dict.t(correct_action) if correct_action else ""
        
        for button in self.answer_buttons.buttons():
            button_text = button.text()
            
            # Disable button (regardless of opacity)
            button.setEnabled(False)
            
            # Determine button state, border, and opacity
            if button_text == correct_action_text:
                # Correct answer - green border
                button.setStyleSheet("""
                    QPushButton {
                        padding: 2px 10px;
                        border: 7px solid #00ad00;
                        border-radius: 6px;
                        background-color: white;
                        color: black;
                    }
                """)
                opacity = 1.0
            elif button_text == self.selected_answer and button_text != correct_action_text:
                # Incorrect selected answer - red border
                button.setStyleSheet("""
                    QPushButton {
                        padding: 2px 10px;
                        border: 7px solid #ff0000;
                        border-radius: 6px;
                        background-color: white;
                        color: black;
                    }
                """)
                opacity = 1.0
            elif button_text == self.selected_answer and button_text == correct_action_text:
                # Correct selected answer - green border
                button.setStyleSheet("""
                    QPushButton {
                        padding: 2px 10px;
                        border: 7px solid #00ad00;
                        border-radius: 6px;
                        background-color: white;
                        color: black;
                    }
                """)
                opacity = 1.0
            else:
                # Others - no border, low opacity
                button.setStyleSheet("""
                    QPushButton {
                        padding: 8px 16px;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        background-color: white;
                    }
                """)
                opacity = 0.8
            
            opacity_effect = QGraphicsOpacityEffect()
            opacity_effect.setOpacity(opacity)
            button.setGraphicsEffect(opacity_effect)

    def update_hands_tiles_feedback(self, correct_tiles):
        """Update hands tiles with correct/incorrect feedback"""

        if not hasattr(self, 'tile_labels') or not self.tile_labels:
            return
        
        user_selected_tile_value = None
        if self.selected_tile is not None:
            for tile_label in self.tile_labels:
                if (hasattr(tile_label, 'tile_index') and 
                    tile_label.tile_index == self.selected_tile and
                    hasattr(tile_label, 'tile_value')):
                    user_selected_tile_value = tile_label.tile_value
                    break

        user_correct = user_selected_tile_value in correct_tiles if user_selected_tile_value else False
        
        # From left to right, find correct ones
        correct_tile_positions = []
        for i, tile_label in enumerate(self.tile_labels):
            if (hasattr(tile_label, 'tile_value') and 
                tile_label.tile_value in correct_tiles):
                correct_tile_positions.append((i, tile_label))

        correct_tile_positions.sort(key=lambda x: x[0])

        tiles_to_highlight = []
        
        if user_correct:
            # 1a. Users' correct answer
            for i, tile_label in enumerate(self.tile_labels):
                if (hasattr(tile_label, 'tile_index') and 
                    tile_label.tile_index == self.selected_tile and
                    hasattr(tile_label, 'tile_value') and
                    tile_label.tile_value in correct_tiles):
                    tiles_to_highlight.append((i, tile_label, "correct"))
                    break
            
            # 1b. Other correct answers' leftmost tile
            remaining_correct_tiles = correct_tiles.copy()
            if user_selected_tile_value:
                remaining_correct_tiles.remove(user_selected_tile_value)
            
            for correct_tile in remaining_correct_tiles:
                for i, tile_label in enumerate(self.tile_labels):
                    if (hasattr(tile_label, 'tile_value') and 
                        tile_label.tile_value == correct_tile and
                        (i, tile_label) not in [(pos, lbl) for pos, lbl, _ in tiles_to_highlight]):
                        tiles_to_highlight.append((i, tile_label, "correct"))
                        break
        
        else:
            # 2a: User's wrong. All the correct answers' leftmost tile
            for correct_tile in correct_tiles:
                for i, tile_label in enumerate(self.tile_labels):
                    if (hasattr(tile_label, 'tile_value') and 
                        tile_label.tile_value == correct_tile and
                        (i, tile_label) not in [(pos, lbl) for pos, lbl, _ in tiles_to_highlight]):
                        tiles_to_highlight.append((i, tile_label, "correct"))
                        break

        for i, tile_label in enumerate(self.tile_labels[:]):
            try:
                if hasattr(tile_label, 'tile_value') and hasattr(tile_label, 'original_pixmap'):
                    is_selected_tile = (hasattr(tile_label, 'tile_index') and 
                                    tile_label.tile_index == self.selected_tile)

                    is_highlighted = False
                    highlight_type = None
                    for pos, lbl, h_type in tiles_to_highlight:
                        if i == pos and tile_label == lbl:
                            is_highlighted = True
                            highlight_type = h_type
                            break

                    # Similar to above
                    if is_selected_tile and is_highlighted and highlight_type == "correct":
                        # User Correct
                        border_color = QColor("#00ad00")
                        opacity = 1.0
                    elif is_selected_tile and not is_highlighted:
                        # User Wrong
                        border_color = QColor("#ff0000")
                        opacity = 1.0
                    elif is_highlighted and highlight_type == "correct":
                        # Other correct
                        border_color = QColor("#00ad00")
                        opacity = 1.0
                    else:
                        # Others
                        border_color = Qt.transparent
                        opacity = 0.4
                    
                    opacity_effect = QGraphicsOpacityEffect()
                    opacity_effect.setOpacity(opacity)
                    tile_label.setGraphicsEffect(opacity_effect)
                    
                    if border_color != Qt.transparent:
                        new_pixmap = self.create_tile_pixmap_with_border(
                            tile_label.original_pixmap, 
                            border_color
                        )
                        tile_label.setPixmap(new_pixmap)
                    else:
                        tile_label.setPixmap(tile_label.original_pixmap)
                        
            except RuntimeError:
                self.tile_labels.remove(tile_label)

    def create_tile_pixmap_with_border(self, original_pixmap, border_color):
        """Create tile pixmap with appropriate border color"""

        pixmap_with_border = QPixmap(original_pixmap.size())
        pixmap_with_border.fill(Qt.transparent)
        
        painter = QPainter(pixmap_with_border)
        
        painter.drawPixmap(0, 0, original_pixmap)
        
        # Draw border if needed
        if border_color != Qt.transparent:
            pen = QPen(border_color)
            pen.setWidth(8)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            from PyQt5.QtCore import QRectF
            rect = pixmap_with_border.rect()
            border_rect = QRectF(3, 3, rect.width() - 6, rect.height() - 6)
            corner_radius = 6
            
            painter.drawRoundedRect(border_rect, corner_radius, corner_radius)
        
        painter.end()
        return pixmap_with_border

    def update_career_stats(self, is_correct):
        """Update career statistics for the current entry"""

        if not self.current_entry:
            return
        
        # Use entry id and get data
        entry_id = self.current_entry['id']
        all_entries = self.data_manager.load_all_data()
        
        if entry_id in all_entries:
            current_encounter = all_entries[entry_id].get('encounter', 0)
            all_entries[entry_id]['encounter'] = current_encounter + 1
            
            if is_correct:
                current_correct = all_entries[entry_id].get('correct', 0)
                all_entries[entry_id]['correct'] = current_correct + 1
            
            # Calculate accuracy
            encounter = all_entries[entry_id].get('encounter', 0)
            correct = all_entries[entry_id].get('correct', 0)
            if encounter > 0:
                accuracy_percent = (correct / encounter) * 100
                all_entries[entry_id]['accuracy'] = f"{accuracy_percent:.1f}%"
            else:
                all_entries[entry_id]['accuracy'] = "N/A %"
            
            self.data_manager.save_data(all_entries)
            
            self.current_entry['data'] = all_entries[entry_id]

    def show_notes_content(self):
        """Simply update the existing labels to show notes content"""

        if not hasattr(self, 'quiz_content') or not self.quiz_content:
            return
        
        # Get notes data
        notes_title = Dict.t("upload.notes")+"\n"
        notes_content = self.current_entry['data'].get('notes', '') if self.current_entry else ''
        
        # Find the content widget
        content_widget = self.quiz_content.findChild(QWidget, "introContentWidget")
        if not content_widget:
            return
        
        # Find title and content labels by their object names
        title_label = content_widget.findChild(QLabel, "introTitleLabel")
        content_label = content_widget.findChild(QLabel, "introContentLabel")
        
        # Check if correct
        is_correct = self.validate_answer() if hasattr(self, 'is_current_submitted') and self.is_current_submitted else False
        if is_correct:
            '''result_text = Dict.t("quiz.correct")'''
            result_text = "〇   "
            color = "#00ad00"
        else:
            '''result_text = Dict.t("quiz.incorrect")'''
            result_text = "✕   "
            color = "#ff0000"

        # Update result label in top right
        if hasattr(self, 'result_label'):
            self.result_label.setText(result_text)
            self.result_label.setStyleSheet(f"""
                QLabel {{
                    padding: 8px;
                    color: {color};
                    font-weight: bold;
                }}
            """)
            self.result_label.show()

        '''result_label = QLabel(result_text)
        result_label.setAlignment(Qt.AlignCenter)
        result_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: bold;
            }}
        """)
        
        apply_font_to_widgets([result_label])

        content_layout = content_widget.layout()
        if content_layout:
            content_layout.insertWidget(0, result_label)'''
        
        if title_label:
            title_label.setText(notes_title)
            title_label.setStyleSheet("""
                QLabel {
                    color: #0056B3;
                    font-weight: bold;
                }
            """)
        
        if content_label:
            content_label.setText(notes_content)
            content_label.setStyleSheet("""
                QLabel {
                    color: #0056B3;
                }
            """)

    def next_question(self):
        """Move to next question"""

        # Hide result label when moving to next question
        if hasattr(self, 'result_label'):
            self.result_label.hide()

        # Count always +1
        self.total_question_count += 1
        
        # Check if quiz should end (non-endless mode)
        endless_mode = self.settings.get("endless", False)
        if not endless_mode and self.current_question_index >= len(self.question_queue) - 1:
            # Quiz finished in non-endless mode
            self.show_quiz_finish_dialog()
            return
        
        # Move to next question in queue
        self.current_question_index += 1
        
        # In endless mode, if gone through all questions, reset to 0
        if endless_mode and self.current_question_index >= len(self.question_queue):
            self.current_question_index = 0
        
        # Reset answer selection
        self.selected_answer = None
        self.selected_tile = None
        
        # Reset answer button states
        self.update_answer_button_states()
        
        # Reset submit button
        self.submit_btn.setText(Dict.t("quiz.submit"))
        self.submit_btn.clicked.disconnect()
        self.submit_btn.clicked.connect(self.submit_answer)
        self.submit_btn.setEnabled(False)
        
        '''# Hide timer
        self.timer_label.hide()'''

        # Update progress display for new question
        self.update_progress_display()
        self.display_question()
        self.update_window_title()

        self.select_discard_if_only_option()
    
    def show_quiz_finish_dialog(self):
        """Show quiz finish dialog with statistics in non-endless"""

        total_questions = len(self.question_queue)
        correct_answers = getattr(self, 'correct_count', 0)
        total_answered = getattr(self, 'total_answered', 0)
        
        accuracy = (correct_answers / total_answered * 100) if total_answered > 0 else 0

        finish_message = Dict.t("quiz.finish").format(total_answered, correct_answers, f"{accuracy:.1f}")

        StyledMessageBox.information(self, Dict.t("quiz.finish_title"), finish_message).exec_()
        
        self.end_quiz()
    
    # --- Question number and Timer --- #

    def update_timer(self):
        """Update timer display"""

        self.timer_label.setText(Dict.t("quiz.timer").format(self.time_remaining))
        
        if self.time_remaining <= 5:
            self.timer_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    color: red;
                    font-weight: bold;
                }
            """)
        else:
            self.timer_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    color: black;
                    font-weight: bold;
                }
            """)

        if self.time_remaining == 0:
            self.timer.stop()
            self.auto_submit_on_timeout()
        else:
            self.time_remaining -= 1
    
    def auto_submit_on_timeout(self):
        """Auto submit when time runs out - select first available option and last tile"""

        if not self.submit_btn.isEnabled() and self.submit_btn.text() == Dict.t("quiz.next"):
            return
        
        # Choose the first answer choice
        if hasattr(self, 'answer_buttons') and self.answer_buttons.buttons():
            available_buttons = self.answer_buttons.buttons()
            if available_buttons:
                first_button = available_buttons[0]
                self.on_answer_selected(first_button)
        
        # Choose the last tile
        if (hasattr(self, 'tile_labels') and self.tile_labels and 
            self.selected_answer != Dict.t("answer.skip")):
            last_tile_index = len(self.tile_labels) - 1
            self.on_tile_selected(last_tile_index)
        
        # Auto submit
        if self.submit_btn.isEnabled():
            self.submit_answer()
        else:
            if hasattr(self, 'answer_buttons') and self.answer_buttons.buttons():
                first_button = self.answer_buttons.buttons()[0]
                self.on_answer_selected(first_button)
                
                if first_button.text() != Dict.t("answer.skip") and hasattr(self, 'tile_labels') and self.tile_labels:
                    last_tile_index = len(self.tile_labels) - 1
                    self.on_tile_selected(last_tile_index)
                
                if self.submit_btn.isEnabled():
                    self.submit_answer()
    
    def update_progress_display(self):
        """Update the progress label display"""

        if hasattr(self, 'progress_label'):
            display_correct = getattr(self, 'correct_count', 0)
            display_total = getattr(self, 'total_answered', 0)
            
            self.progress_label.setText(f"   Q{self.total_question_count} ({display_correct}/{display_total})")

    def update_progress_stats(self, is_correct):
        """Update progress statistics"""

        if not hasattr(self, 'correct_count'):
            self.correct_count = 0
        if not hasattr(self, 'total_answered'):
            self.total_answered = 0
        
        self.total_answered += 1
        if is_correct:
            self.correct_count += 1

    def reset_progress_stats(self):
        """Reset progress statistics when starting new quiz"""

        self.correct_count = 0
        self.total_answered = 0

    # --- Quit and End --- #

    def quit_quiz(self):
        """Quit the quiz"""
        
        reply = StyledMessageBox.question(
            self, 
            Dict.t("common.confirm"), 
            Dict.t("quiz.quit_confirm"),
            confirm_red=True
        )
        
        if reply.exec_() == QMessageBox.Yes:
            self.end_quiz()
    
    def end_quiz(self):
        """End the quiz and return to initial layout"""

        self.is_quiz_active = False

        self.timer.stop()
        self.create_initial_layout()
        self.update_filter_button_style()

        self.apply_font()
        self.reset_window_title()

        self.quiz_ended.emit()
    
    # --- UI Update Methods ---#

    def showEvent(self, event):
        """Called when the page becomes visible to refresh page"""

        super().showEvent(event)
        self.refresh_quiz_data()
        self.apply_font()

    def apply_font(self):
        """Apply font settings to all widgets"""
        
        widgets = []
        
        all_widgets = self.findChildren((QLabel, QPushButton, QComboBox, QLineEdit))
        widgets.extend(all_widgets)
        
        if widgets:
            apply_font_to_widgets(widgets)