import os
import json
import uuid
import shutil
import zipfile
from datetime import datetime
from collections import Counter, OrderedDict
from PyQt5.QtWidgets import (   QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QScrollArea, QFrame, QGridLayout, 
                                QComboBox, QLineEdit, QGroupBox, QCheckBox,
                                QApplication, QSizePolicy, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFontMetrics, QIntValidator

try:
    from pypinyin import pinyin, Style
    HAS_PINYIN = True
except ImportError:
    HAS_PINYIN = False

from src.utils.i18n import Dict
from src.utils.format_applier import apply_font_to_widgets
from src.utils.settings_manager import SettingsManager

from src.widgets.hint_dialog import StyledMessageBox

class LibraryPage(QWidget):

    back_clicked = pyqtSignal()
    entry_edit_requested = pyqtSignal(str)  # Signal to request editing an entry
    
    def __init__(self, data_manager):

        super().__init__()
        self.data_manager = data_manager
        # self.settings_manager = SettingsManager()

        self.current_layout = "list"

        self.selection_mode = False  # Batch selection mode
        self.selected_entries = OrderedDict()  # Selected entry IDs

        self.current_search_tiles = ""  # Searching tiles
        self.is_searching = False       # If in hands searching mode
        
        # Pagination state
        self.current_page = 1
        self.page_size = 30
        self.total_pages = 1
        
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
        self.is_filtering = False       # If in filter mode

        self.init_ui()
        self.load_library()
        self.apply_font()

    # --- UI Initialization --- #
    
    def init_ui(self):

        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Top toolbar - first row
        toolbar_row1 = QHBoxLayout()
        
        # Left: Layout selection and sorting
        left_toolbar = QHBoxLayout()
        
        # Layout selection
        layout_layout = QHBoxLayout()
        self.layout_label = QLabel(Dict.t("library.layout"))
        self.layout_label.setStyleSheet("QLabel{padding:8;}")
        layout_layout.addWidget(self.layout_label)

        self.layout_combo = QComboBox()
        self.layout_combo.setStyleSheet("QComboBox{padding:8;}")
        self.layout_combo.addItems([
            Dict.t("library.list_view"),
            Dict.t("library.grid_view")
        ])
        self.layout_combo.setCurrentIndex(0)
        self.layout_combo.currentTextChanged.connect(self.change_layout)
        layout_layout.addWidget(self.layout_combo)
        left_toolbar.addLayout(layout_layout)
        
        # Sort options
        sort_layout = QHBoxLayout()
        '''self.sort_label = QLabel(Dict.t("library.sort"))
        self.sort_label.setStyleSheet("QLabel{padding:8;}")
        sort_layout.addWidget(self.sort_label)'''

        self.sort_combo = QComboBox()
        self.sort_combo.setStyleSheet("QComboBox{padding:8;}")
        sort_options = [
            "library.latest", "library.oldest",
            "library.title_az", "library.title_za", 
            "library.turn_asc", "library.turn_desc",
            "library.difficulty_asc", "library.difficulty_desc",
            "library.encounter_asc", "library.encounter_desc",
            "library.accuracy_asc", "library.accuracy_desc"
        ]
        for option in sort_options:
            self.sort_combo.addItem(Dict.t(option), option)
        sort_layout.addWidget(self.sort_combo)
        
        # Items per page
        items_per_page_layout = QHBoxLayout()
        '''self.items_per_page_label = QLabel(Dict.t("library.items_per_page"))
        self.items_per_page_label.setStyleSheet("QLabel{padding:8;}")
        items_per_page_layout.addWidget(self.items_per_page_label)'''
        
        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.setStyleSheet("QComboBox{padding:8;}")
        self.items_per_page_combo.addItems(["20", "30", "50", "80", "100", "200", "300", "500", "1000"])
        self.items_per_page_combo.setCurrentText("30")
        self.items_per_page_combo.setMaximumWidth(100)
        self.items_per_page_combo.currentTextChanged.connect(self.on_page_size_changed)
        items_per_page_layout.addWidget(self.items_per_page_combo)
        
        # Page navigation
        self.page_jump_input = QLineEdit()
        self.page_jump_input.setStyleSheet("QLineEdit{padding:8;}")
        self.page_jump_input.setPlaceholderText(Dict.t("library.page_jump_placeholder"))
        self.page_jump_input.setMaximumWidth(100)
        self.page_jump_input.setValidator(QIntValidator(0, 999999999))
        self.page_jump_input.returnPressed.connect(self.on_page_jump)
        items_per_page_layout.addWidget(self.page_jump_input)
        
        self.page_info_label = QLabel()
        self.page_info_label.setStyleSheet("QLabel{padding:8;}")
        self.page_info_label.setToolTip(Dict.t("library.page_info"))
        items_per_page_layout.addWidget(self.page_info_label)
        
        left_toolbar.addLayout(sort_layout)
        left_toolbar.addLayout(items_per_page_layout)
        
        toolbar_row1.addLayout(left_toolbar)
        
        toolbar_row1.addStretch()
        
        # Right: Batch selection button, and select ALL
        self.batch_select_btn = QPushButton(Dict.t("library.batch_select"))
        self.batch_select_btn.setStyleSheet("QPushButton{padding:8;}")
        self.batch_select_btn.clicked.connect(self.toggle_batch_selection)
        toolbar_row1.addWidget(self.batch_select_btn)

        self.select_all_btn = QPushButton(Dict.t("library.select_all"))
        self.select_all_btn.setStyleSheet("QPushButton{padding:8;}")
        self.select_all_btn.setEnabled(False)
        self.select_all_btn.clicked.connect(self.select_all_visible)
        toolbar_row1.addWidget(self.select_all_btn)
        
        layout.addLayout(toolbar_row1)
        
        # Top toolbar - second row
        toolbar_row2 = QHBoxLayout()
        
        # Left: Filter button, Hands search button, and Search bar
        # Filter label
        self.row2_layout_label = QLabel(Dict.t("library.filter"))
        self.row2_layout_label.setStyleSheet("QLabel{padding:8;}")
        toolbar_row2.addWidget(self.row2_layout_label)

        # Filter button
        self.filter_btn = QPushButton(Dict.t("library.filter_search"))
        self.filter_btn.setStyleSheet("QPushButton{padding:8;}")
        self.filter_btn.clicked.connect(self.open_filter_dialog)
        toolbar_row2.addWidget(self.filter_btn)
        
        # Hand search button
        self.hands_search_btn = QPushButton(Dict.t("library.hands_search"))
        self.hands_search_btn.setStyleSheet("QPushButton{padding:8;}")
        self.hands_search_btn.clicked.connect(self.open_hands_search)
        toolbar_row2.addWidget(self.hands_search_btn)
        
        # Entry count display (shown/total) now placed here next to filter & hands
        self.entry_count_label = QLabel()
        self.entry_count_label.setStyleSheet("QLabel{padding:8;}")
        toolbar_row2.addWidget(self.entry_count_label)
        
        toolbar_row2.addStretch()
        
        # Right: (Career), Delete, Export, Import buttons
        right_toolbar = QHBoxLayout()

        # Reset Career button
        self.reset_career_btn = QPushButton(Dict.t("library.reset_career"))
        self.reset_career_btn.setStyleSheet("QPushButton{padding:8;}")
        self.reset_career_btn.setEnabled(False)
        self.reset_career_btn.clicked.connect(self.reset_career_selected)
        right_toolbar.addWidget(self.reset_career_btn)
        
        # Delete button
        self.delete_btn = QPushButton(Dict.t("library.delete"))
        self.delete_btn.setStyleSheet("QPushButton{padding:8;}")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected)
        right_toolbar.addWidget(self.delete_btn)
        
        # Export button
        self.export_btn = QPushButton(Dict.t("library.export"))
        self.export_btn.setStyleSheet("QPushButton{padding:8;}")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_selected)
        right_toolbar.addWidget(self.export_btn)
        
        # Import button
        self.import_btn = QPushButton(Dict.t("library.import"))
        self.import_btn.setStyleSheet("QPushButton{padding:8;}")
        self.import_btn.clicked.connect(self.import_entries)
        right_toolbar.addWidget(self.import_btn)
        
        toolbar_row2.addLayout(right_toolbar)
        
        layout.addLayout(toolbar_row2)
        
        # Scroll area for entry display
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #FFFFFF;
                border: 1px solid #FFFFFF;
            }
        """)
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(12)
        self.scroll_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
        
        self.sort_combo.currentTextChanged.connect(self.apply_filters)

    # --- Import/Export Methods --- #
    
    def export_selected(self):
        """Export selected entries to ZIP file"""

        if not self.selected_entries:
            return
        
        # Confirmation dialog
        if not self.show_confirmation(
            Dict.t("msg.hint"),
            Dict.t("library.export_confirm_message").format(len(self.selected_entries)),
            need_blue=True
        ):
            return
        
        try:
            # Create export directory if not exists
            export_dir = os.path.join("saves", "export")
            os.makedirs(export_dir, exist_ok=True)
            
            # Create temporary directory for export
            temp_dir = os.path.join(export_dir, "temp_export")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # Create images directory
            images_dir = os.path.join(temp_dir, "images")
            os.makedirs(images_dir)
            
            # Collect selected entries data and copy images
            export_data = {}
            for entry_id in self.selected_entries:
                if entry_id in self.entries:
                    entry_data = self.entries[entry_id].copy()
                    export_data[entry_id] = entry_data
                    
                    # Copy image file if exists
                    image_path = self.data_manager.get_image_path(entry_id)
                    if image_path and os.path.exists(image_path):
                        image_filename = os.path.basename(image_path)
                        dest_path = os.path.join(images_dir, image_filename)
                        shutil.copy2(image_path, dest_path)
            
            # Save metadata.json
            metadata_path = os.path.join(temp_dir, "data.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # Create ZIP file
            zip_filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join(export_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            # Success
            StyledMessageBox.information(self, 
                                  Dict.t("library.export_success_title"),
                                  Dict.t("library.export_success_message").format(zip_filename)).exec_()
            
        except Exception as e:
            StyledMessageBox.critical(self,
                               Dict.t("library.export_error_title"),
                               Dict.t("library.export_error_message").format(str(e))).exec_()
    
    def import_entries(self):
        """Import entries from ZIP file"""

        # Exit from batch selection mode
        if self.selection_mode:
            self.reset_selection_mode()
            
        try:
            # Open file dialog to select ZIP file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                Dict.t("library.import_dialog_title"),
                "",
                "ZIP Files (*.zip)"
            )
            
            if not file_path:
                return
            
            # Create temporary directory for import
            import_dir = os.path.join("saves", "import")
            os.makedirs(import_dir, exist_ok=True)
            
            temp_dir = os.path.join(import_dir, "temp_import")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # Extract ZIP file
            with zipfile.ZipFile(file_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Load imported data
            data_path = os.path.join(temp_dir, "data.json")
            if not os.path.exists(data_path):
                raise ValueError("ZIP file does not contain data.json")
            
            with open(data_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Load current data
            current_data = self.data_manager.load_entries()
            
            # Process images directory
            images_dir = os.path.join(temp_dir, "images")
            imported_images = {}
            if os.path.exists(images_dir):
                for image_file in os.listdir(images_dir):
                    image_path = os.path.join(images_dir, image_file)
                    if os.path.isfile(image_path):
                        imported_images[image_file] = image_path
            
            # Merge data and handle UUID conflicts
            merged_count = 0
            image_conflict_count = 0
            
            for entry_id, entry_data in imported_data.items():
                if entry_id not in current_data:
                    # No conflict, add directly
                    current_data[entry_id] = entry_data
                    merged_count += 1
                    
                    # Copy image file if exists
                    image_filename = entry_data.get('image_filename', '')
                    if image_filename and image_filename in imported_images:
                        dest_path = os.path.join(self.data_manager.images_dir, image_filename)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(imported_images[image_filename], dest_path)
                else:
                    # UUID conflict, generate new UUID
                    new_entry_id = str(uuid.uuid4())
                    entry_data['id'] = new_entry_id
                    current_data[new_entry_id] = entry_data
                    merged_count += 1
                    
                    # Copy image file with new ID
                    image_filename = entry_data.get('image_filename', '')
                    if image_filename and image_filename in imported_images:
                        # Update image filename to match new UUID
                        file_ext = os.path.splitext(image_filename)[1]
                        new_image_filename = f"{new_entry_id}{file_ext}"
                        entry_data['image_filename'] = new_image_filename
                        
                        dest_path = os.path.join(self.data_manager.images_dir, new_image_filename)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(imported_images[image_filename], dest_path)
                        image_conflict_count += 1
            
            # Save merged data
            self.data_manager.save_data(current_data)
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            # Show result message
            message = Dict.t("library.import_success_message").format(merged_count)
            if image_conflict_count > 0:
                message += f"\n{Dict.t('library.import_conflict_message').format(image_conflict_count)}"
            
            # Success
            StyledMessageBox.information(self,
                                  Dict.t("library.import_success_title"),
                                  message).exec_()
            
            # Refresh library to show
            self.reset_to_page_one()
            self.load_library()
            
        except Exception as e:
            StyledMessageBox.critical(self,
                               Dict.t("library.import_error_title"),
                               Dict.t("library.import_error_message").format(str(e))).exec_()
    
    # --- Toolbar Action Methods --- #

    # Hands

    def open_hands_search(self):
        """Call TileSelector"""

        if self.selection_mode:
            self.reset_selection_mode()

        from src.widgets.tile_selector import TileSelector
        
        search_dialog = TileSelector(
            parent=self,
            mode="search",
            current_selection=self.current_search_tiles
        )
        
        search_dialog.selection_completed.connect(self.on_hands_search_completed)
        
        search_dialog.exec_()

    def clear_hands_search(self):

        self.current_search_tiles = ""
        self.is_searching = False
        
        self.apply_filters()
        
        self.update_hands_search_button_style()

    def on_hands_search_completed(self, search_tiles):

        self.current_search_tiles = search_tiles
        self.is_searching = bool(search_tiles)
        
        self.apply_filters()
        
        self.update_hands_search_button_style()

    def update_hands_search_button_style(self):

        if self.is_searching and self.current_search_tiles:
            self.hands_search_btn.setStyleSheet("""
                QPushButton {
                    padding: 7px;
                    background-color: #e0eef9;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0eef9;
                }
            """)
        else:
            self.hands_search_btn.setStyleSheet("QPushButton{padding:8;}")

    # Filter

    def open_filter_dialog(self):
        """Call EntryFilter dislog"""

        # Exit from batch selection mode
        if self.selection_mode:
            self.reset_selection_mode()

        from src.widgets.entry_filter import EntryFilterDialog
        
        filter_dialog = EntryFilterDialog(self)
        filter_dialog.set_filter_state(self.filter_state)
        
        if filter_dialog.exec_() == filter_dialog.Accepted:
            self.filter_state = filter_dialog.get_filter_state()
            self.is_filtering = any([
                self.filter_state['text_contains']['text'] and self.filter_state['text_contains']['fields'],
                self.filter_state['text_excludes']['text'] and self.filter_state['text_excludes']['fields'],
                self.filter_state['source'],
                self.filter_state['players'],
                self.filter_state['image'],
                self.filter_state['wind'],
                self.filter_state['self_wind'],
                self.filter_state['game'],
                (self.filter_state['difficulty_min'] > 0 or self.filter_state['difficulty_max'] < 100),
                (self.filter_state['accuracy_min'] > 0 or self.filter_state['accuracy_max'] < 100),
                self.filter_state['start_date'] is not None,
                self.filter_state['end_date'] is not None
            ])
            
            self.reset_to_page_one()
            self.apply_filters()
            self.update_filter_button_style()

    def clear_filter(self):
        """Clear the filter conditions"""

        self.filter_state = {
            'text_contains': {'text': '', 'fields': []},
            'text_excludes': {'text': '', 'fields': []},
            'source': [],
            'players': [],
            'image': [],
            'wind': [],
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
        self.is_filtering = False
        
        self.reset_to_page_one()
        self.apply_filters()
        self.update_filter_button_style()

    def update_filter_button_style(self):
        """When filter applies, update style to give blue border"""
        
        if self.is_filtering:
            self.filter_btn.setStyleSheet("""
                QPushButton {
                    padding: 7px;
                    background-color: #e0eef9;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0eef9;
                }
            """)
        else:
            self.filter_btn.setStyleSheet("QPushButton{padding:8;}")

    # Career

    def reset_career_selected(self):

        if not self.selected_entries:
            return
        
        # Confirm
        if not self.show_confirmation(
            Dict.t("msg.hint"),
            Dict.t("library.reset_career_confirm_message").format(len(self.selected_entries)),
            need_red=True
        ):
            return
        
        try:
            current_data = self.data_manager.load_all_data()
            
            # Reset career to 0
            reset_count = 0
            for entry_id in self.selected_entries:
                if entry_id in current_data:
                    entry_data = current_data[entry_id]
                    entry_data['encounter'] = 0
                    entry_data['correct'] = 0
                    entry_data['accuracy'] = "N/A %"
                    reset_count += 1

            self.data_manager.save_data(current_data)
            
            StyledMessageBox.information(self,
                                  Dict.t("library.reset_career_success_title"),
                                  Dict.t("library.reset_career_success_message").format(reset_count)).exec_()

            self.selected_entries.clear()
            self.toggle_batch_selection()
            
            self.load_library()
            
        except Exception as e:
            StyledMessageBox.critical(self,
                               Dict.t("library.reset_career_error_title"),
                               Dict.t("library.reset_career_error_message").format(str(e))).exec_()

    # Delete

    def delete_selected(self):
        """Delete selected entries"""

        if not self.selected_entries:
            return
        
        # Confirmation dialog (red)
        if not self.show_confirmation(
            Dict.t("msg.hint"),
            Dict.t("library.delete_confirm_message").format(len(self.selected_entries)),
            need_red=True
        ):
            return
        
        try:
            # Load current data
            current_data = self.data_manager.load_all_data()
            
            # Remove selected entries and their images
            deleted_count = 0
            for entry_id in self.selected_entries:
                if entry_id in current_data:
                    # Remove entry from data
                    del current_data[entry_id]
                    deleted_count += 1
                    
                    # Remove image file if exists
                    image_path = self.data_manager.get_image_path(entry_id)
                    if image_path and os.path.exists(image_path):
                        os.remove(image_path)
            
            # Save updated data
            self.data_manager.save_data(current_data)
            
            # Show success message
            StyledMessageBox.information(self,
                                  Dict.t("library.delete_success_title"),
                                  Dict.t("library.delete_success_message").format(deleted_count)).exec_()
            
            # Clear selection and exit selection mode
            self.selected_entries.clear()
            self.toggle_batch_selection()
            
            # Refresh library
            self.reset_to_page_one()
            self.load_library()
            
        except Exception as e:
            StyledMessageBox.critical(self,
                               Dict.t("library.delete_error_title"),
                               Dict.t("library.delete_error_message").format(str(e))).exec_()

    # Batch Select Mode

    def toggle_batch_selection(self):
        """Toggle batch selection mode"""

        self.selection_mode = not self.selection_mode
        self.selected_entries.clear()
        
        if self.selection_mode:

            self.batch_select_btn.setText(Dict.t("library.cancel_selection"))

            self.reset_career_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.select_all_btn.setEnabled(True)

            # Apply selected style to batch select button
            self.batch_select_btn.setStyleSheet("""
                    QPushButton {
                    padding: 7px;
                    background-color: #e0eef9;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                }
                    QPushButton:hover {
                        background-color: #e0eef9;
                    }
            """)
        else:

            self.batch_select_btn.setText(Dict.t("library.batch_select"))

            self.reset_career_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.select_all_btn.setEnabled(False)

            self.batch_select_btn.setStyleSheet("QPushButton{padding:8;}")
        
        self.update_selection_styles()

    def reset_selection_mode(self):
        """Reset selection mode (=cancel selection)"""

        if self.selection_mode:
            self.selection_mode = False
            self.selected_entries.clear()

            self.batch_select_btn.setText(Dict.t("library.batch_select"))
            self.batch_select_btn.setStyleSheet("QPushButton{padding:8;}")

            self.reset_career_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.select_all_btn.setEnabled(False)

            self.update_selection_styles()
            self.update_hands_search_button_style()
            self.update_filter_button_style()

    def select_all_visible(self):
        "Select all"

        if not self.selection_mode:
            return
        
        # Only select those on current page
        '''visible_entry_ids = set()
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                entry_id = getattr(widget, 'entry_id', None)
                if entry_id is not None:
                    visible_entry_ids.add(entry_id)
        
        self.selected_entries = visible_entry_ids.copy()'''

        self.selected_entries.clear()
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                entry_id = getattr(widget, 'entry_id', None)
                if entry_id is not None:
                    self.selected_entries[entry_id] = True
        
        self.update_selection_styles()
        
        has_selection = len(self.selected_entries) > 0
        self.delete_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
        self.reset_career_btn.setEnabled(has_selection)

    def update_selection_styles(self):
        """Update selection styles for all entries"""

        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()

                # Only process frames with entry_id attribute (entry frames)
                entry_id = getattr(widget, 'entry_id', None)
                if entry_id is not None:  # Only entry frames have entry_id
                    if entry_id in self.selected_entries:
                        # Only modify border: blue
                        widget.setStyleSheet("""
                            #main_frame {
                                border: 1px solid #0078d4;
                                background-color: #E0EEF9;
                            }
                        """)
                    else:
                        widget.setStyleSheet("""
                            #main_frame {
                                border: 1px solid #000000;
                            }
                            #main_frame:hover {
                                border: 1px solid #0078d4;
                                background-color: #f8fbff;
                            }
                        """)  # Restore default style with hover
    
    def toggle_entry_selection(self, entry_id, widget):
        """Switch selected / not selected on entry"""

        if entry_id in self.selected_entries:
            '''self.selected_entries.discard(entry_id)'''
            del self.selected_entries[entry_id]
            widget.setStyleSheet("""
                #main_frame {
                    border: 1px solid #000000;
                }
                #main_frame:hover {
                    border: 1px solid #0078d4;
                    background-color: #f8fbff;
                }
            """)
        else:
            '''self.selected_entries.add(entry_id)'''
            self.selected_entries[entry_id] = True
            widget.setStyleSheet("""
                #main_frame {
                    border: 1px solid #0078d4; 
                    background-color: #E0EEF9;
                }
            """)
        
        has_selection = len(self.selected_entries) > 0
        self.delete_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
        self.reset_career_btn.setEnabled(has_selection)

    # Mouse Event

    def setup_drag_selection(self, frame):
        """Drag mouse for multi select"""

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                # print(f"Mouse pressed on entry: {frame.entry_id}")
                
                if self.selection_mode:
                    frame.is_dragging = True
                    # Drag start's status
                    frame.drag_start_selected = (frame.entry_id in self.selected_entries)
                    # Current entry's status
                    self.toggle_entry_selection(frame.entry_id, frame)
                else:
                    # Normal: Call editor
                    # print("Debug: Opening editor in normal mode")
                    self.open_entry_editor(frame.entry_id)
            else:
                QFrame.mousePressEvent(frame, event)
        
        def mouseMoveEvent(event):
            if self.selection_mode and frame.is_dragging and event.buttons() & Qt.LeftButton:
                pos = frame.mapToGlobal(event.pos())
                widget = QApplication.widgetAt(pos)
                
                while widget and not hasattr(widget, 'entry_id'):
                    widget = widget.parent()
                
                if widget and hasattr(widget, 'entry_id'):
                    entry_id = widget.entry_id
                    current_selected = (entry_id in self.selected_entries)
                    
                    if current_selected != frame.drag_start_selected:
                        # operated so skip
                        pass
                    else:
                        # Same status, switch
                        self.toggle_entry_selection(entry_id, widget)
            else:
                QFrame.mouseMoveEvent(frame, event)
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.LeftButton:
                frame.is_dragging = False
            QFrame.mouseReleaseEvent(frame, event)
        
        frame.mousePressEvent = mousePressEvent
        frame.mouseMoveEvent = mouseMoveEvent
        frame.mouseReleaseEvent = mouseReleaseEvent
    
    '''def on_entry_clicked(self, entry_id, widget):
        # Handle click of entry
        print(f"Entry clicked: {entry_id}")
              
        if not self.selection_mode:
            self.open_entry_editor(entry_id)
            return
        
        # In selection mode, toggle selection state
        self.toggle_entry_selection(entry_id, widget)'''

    # --- Data Edit --- #

    def open_entry_editor(self, entry_id):

        if entry_id not in self.entries:
            return
        
        # Emit signal to request editing this entry
        self.entry_edit_requested.emit(entry_id)

    # --- Data/Entry Management / Sort Methods --- #
    
    def load_library(self):

        # Load items from library
        self.entries = self.data_manager.load_entries()
        self.apply_filters()
    
    # --- Pagination Methods --- #
    
    def go_to_page(self, page_num):
        """Goto some page"""

        if 1 <= page_num <= self.total_pages:
            if self.selection_mode:
                self.reset_selection_mode()
            
            self.current_page = page_num
            self.apply_filters()
            self.update_pagination_info()
    
    def update_pagination_info(self):

        if hasattr(self, 'page_info_label'):
            self.page_info_label.setText(f"{self.current_page}/{self.total_pages}")
    
    def get_paged_entries(self, entries):
        """Get entries on current page"""

        if not entries:
            return {}
        
        # Calculate
        total_items = len(entries)
        self.total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        # Calculate the entires range
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        # Turns into dict
        entry_list = list(entries.items())
        paged_entries = dict(entry_list[start_idx:end_idx])
        
        return paged_entries
    
    def on_page_size_changed(self, new_size):

        self.page_size = int(new_size)
        self.reset_to_page_one()
        self.apply_filters()
        self.update_pagination_info()
    
    def reset_to_page_one(self):
        
        self.current_page = 1
    
    def on_page_jump(self):
        
        try:
            page_num = int(self.page_jump_input.text())
            self.go_to_page(page_num)
            self.page_jump_input.clear()
        except ValueError:
            self.page_jump_input.clear()
    
    def matches_filter(self, entry_data):
        """Check if an entry matches the current filter - very dogshit to implement."""

        # Collects all filter applied
        filter_results = []
        
        # Include text filter
        if self.filter_state['text_contains']['text'] and self.filter_state['text_contains']['fields']:
            text_contains_match = False
            search_text = self.filter_state['text_contains']['text'].lower()
            
            for field in self.filter_state['text_contains']['fields']:
                if field == 'title':
                    if search_text in entry_data.get('title', '').lower():
                        text_contains_match = True
                        break
                elif field == 'intro':
                    if search_text in entry_data.get('intro', '').lower():
                        text_contains_match = True
                        break
                elif field == 'notes':
                    if search_text in entry_data.get('notes', '').lower():
                        text_contains_match = True
                        break
            
            filter_results.append(text_contains_match)
        
        # Exclude text filter
        if self.filter_state['text_excludes']['text'] and self.filter_state['text_excludes']['fields']:
            text_excludes_match = True  # Default not match, so not excluded
            search_text = self.filter_state['text_excludes']['text'].lower()
            
            for field in self.filter_state['text_excludes']['fields']:
                if field == 'title':
                    if search_text in entry_data.get('title', '').lower():
                        text_excludes_match = False
                        break
                elif field == 'intro':
                    if search_text in entry_data.get('intro', '').lower():
                        text_excludes_match = False
                        break
                elif field == 'notes':
                    if search_text in entry_data.get('notes', '').lower():
                        text_excludes_match = False
                        break
            
            filter_results.append(text_excludes_match)
        
        # Source filter
        if self.filter_state['source']:
            source_match = entry_data.get('source', '') in self.filter_state['source']
            filter_results.append(source_match)
        
        # Players filter
        if self.filter_state['players']:
            players_match = entry_data.get('players', '') in self.filter_state['players']
            filter_results.append(players_match)
        
        # Image filter
        if self.filter_state['image']:
            has_image = bool(entry_data.get('image_filename', ''))
            image_match = False
            if 'common.have' in self.filter_state['image'] and has_image:
                image_match = True
            if 'common.noHave' in self.filter_state['image'] and not has_image:
                image_match = True
            filter_results.append(image_match)
        
        # Wind filter
        if self.filter_state['wind']:
            wind_match = entry_data.get('wind', '') in self.filter_state['wind']
            filter_results.append(wind_match)
        # Self wind filter
        if self.filter_state['self_wind']:
            swind_match = entry_data.get('self_wind', '') in self.filter_state['self_wind']
            filter_results.append(swind_match)
        
        # Game filter
        if self.filter_state['game']:
            game_match = str(entry_data.get('game', '')) in self.filter_state['game']
            filter_results.append(game_match)
        
        # Difficulty filter
        if (self.filter_state['difficulty_min'] > 0 or self.filter_state['difficulty_max'] < 100):
            difficulty = int(entry_data.get('difficulty', 0))
            if difficulty < 0:  # Changed from == 0 to < 0, since 0 should count in filter now...
                difficulty_match = False
            else:
                difficulty_match = (self.filter_state['difficulty_min'] <= difficulty <= self.filter_state['difficulty_max'])
            filter_results.append(difficulty_match)
        
        # Accuracy filter
        if (self.filter_state['accuracy_min'] > 0 or self.filter_state['accuracy_max'] < 100):
            accuracy_str = entry_data.get('accuracy', 'N/A %')
            if accuracy_str == 'N/A %' or not accuracy_str:  # N/A means no accuracy data, filter out
                accuracy_match = False
            else:
                try:
                    if accuracy_str.endswith('%'):
                        accuracy_value = float(accuracy_str[:-1])
                    else:
                        accuracy_value = float(accuracy_str)
                    
                    accuracy_match = (self.filter_state['accuracy_min'] <= accuracy_value <= self.filter_state['accuracy_max']) 
                except (ValueError, TypeError):
                    accuracy_match = False
            filter_results.append(accuracy_match)
        
        # Date filter
        if self.filter_state['start_date'] or self.filter_state['end_date']:
            entry_date_str = entry_data.get('create_time', '')
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

    def apply_filters(self):
        """Apply all filter conditions"""

        # Exit from batch selection mode prevent problems
        if self.selection_mode:
            self.reset_selection_mode()

        filtered_entries = {}
        
        for entry_id, entry_data in self.entries.items():

            # Hands search
            if self.is_searching and self.current_search_tiles:
                if not self.does_entry_contain_tiles(entry_data, self.current_search_tiles):
                    continue

            # Filter search
            if self.is_filtering:
                if not self.matches_filter(entry_data):
                    continue
        
            filtered_entries[entry_id] = entry_data
        
        # Apply sorting
        self.apply_sorting(filtered_entries)
        
        self.update_hands_search_button_style()
        self.update_filter_button_style()
    
    def apply_sorting(self, entries):
        """Sort!"""
        
        sort_type = self.sort_combo.currentData()
        
        if sort_type == "library.latest":
            sorted_entries = dict(  sorted(entries.items(), 
                                    key=lambda x: x[1].get('create_time', ''), 
                                    reverse=True))
        elif sort_type == "library.oldest":
            sorted_entries = dict(  sorted(entries.items(), 
                                    key=lambda x: x[1].get('create_time', '')))

        elif sort_type == "library.title_az":
            sorted_entries = dict(  sorted(entries.items(), 
                                    key=lambda x: self.get_pinyin(x[1].get('title', ''))))
        elif sort_type == "library.title_za":
            sorted_entries = dict(  sorted(entries.items(), 
                                    key=lambda x: self.get_pinyin(x[1].get('title', '')), 
                                    reverse=True))
            
        elif sort_type == "library.turn_asc":
            sorted_entries = dict(sorted(entries.items(), 
                                    key=lambda x: int(x[1].get('turn', 0))))
        elif sort_type == "library.turn_desc":
            sorted_entries = dict(sorted(entries.items(), 
                                    key=lambda x: int(x[1].get('turn', 0)), 
                                    reverse=True))

        elif sort_type == "library.difficulty_asc":
            sorted_entries = dict(  sorted(entries.items(), 
                                    key=lambda x: int(x[1].get('difficulty', 0))))
        elif sort_type == "library.difficulty_desc":
            sorted_entries = dict(  sorted(entries.items(), 
                                    key=lambda x: int(x[1].get('difficulty', 0)), 
                                    reverse=True))

        elif sort_type == "library.encounter_asc":
            sorted_entries = dict(sorted(entries.items(), 
                                    key=lambda x: int(x[1].get('encounter', 0))))
        elif sort_type == "library.encounter_desc":
            sorted_entries = dict(sorted(entries.items(), 
                                    key=lambda x: int(x[1].get('encounter', 0)), 
                                    reverse=True))

        elif sort_type == "library.accuracy_asc":
            sorted_entries = dict(sorted(entries.items(), 
                                    key=lambda x: self.get_accuracy_value(x[1].get('accuracy', 'N/A %'))))
        elif sort_type == "library.accuracy_desc":
            sorted_entries = dict(sorted(entries.items(), 
                                    key=lambda x: self.get_accuracy_value(x[1].get('accuracy', 'N/A %')), 
                                    reverse=True))
        else:
            sorted_entries = entries
        
        # Apply pagination
        paged_entries = self.get_paged_entries(sorted_entries)
        
        # Update entry count with three-part display: current page / filtered / total
        self.update_entry_count(sorted_entries, paged_entries)
        
        self.display_entries(paged_entries)
        self.update_pagination_info()
    
    def update_entry_count(self, filtered_entries, current_page_entries=None):
        """Update the entry count display"""

        filtered_count = len(filtered_entries)
        total_count = len(self.data_manager.load_all_data())
        
        if current_page_entries is not None:
            current_page_count = len(current_page_entries)
            if hasattr(self, 'entry_count_label') and self.entry_count_label is not None:
                self.entry_count_label.setText(f"{current_page_count}/{filtered_count}/{total_count}")
                self.entry_count_label.setToolTip(Dict.t("library.entry_count"))
        else:
            if hasattr(self, 'entry_count_label') and self.entry_count_label is not None:
                self.entry_count_label.setText(f"{filtered_count}/{total_count}")
                self.entry_count_label.setToolTip(Dict.t("library.entry_count"))
    
    def display_entries(self, entries=None):
        """Display entries"""

        if entries is None:
            entries = self.entries
        
        # Clear existing content and release QPixmap resources
        self.clear_layout_with_pixmap_cleanup()
        
        if self.current_layout == "grid":
            self.display_grid_view(entries)
        else:
            self.display_list_view(entries)
        
        self.apply_font()
    
    def clear_layout_with_pixmap_cleanup(self):
        """Clear layout and properly release QPixmap resources"""

        for i in reversed(range(self.scroll_layout.count())): 
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                # Release QPixmap resources before removing widget
                self.release_pixmap_resources(widget)
                # Use deleteLater() for proper Qt cleanup
                widget.deleteLater()
    
    def release_pixmap_resources(self, widget):
        """Recursively release QPixmap resources from widget and its children"""

        # Find all QLabel widgets with pixmaps
        labels = widget.findChildren(QLabel)
        for label in labels:
            if label.pixmap() is not None:
                # Detach the pixmap to release memory
                label.pixmap().detach()
                label.clear()
        
        # Recursively process child widgets
        for child in widget.findChildren(QWidget):
            if child != widget:  # Avoid infinite recursion
                self.release_pixmap_resources(child)
    
    def display_grid_view(self, entries):
        """Grid view display - 4 entries per row"""

        for c in range(self.scroll_layout.columnCount()):
            self.scroll_layout.setColumnStretch(c, 0)

        row, col = 0, 0
        max_cols = 4
        
        for entry_id, entry_data in entries.items():
            item_frame = self.create_item_frame(entry_id, entry_data)
            self.scroll_layout.addWidget(item_frame, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Add flexible space
        self.scroll_layout.setRowStretch(row + 1, 1)
        for c in range(max_cols):
            self.scroll_layout.setColumnStretch(c, 1)
    
    def display_list_view(self, entries):
        """List view display - 2 entries per row"""

        for c in range(self.scroll_layout.columnCount()):
            self.scroll_layout.setColumnStretch(c, 0)
        
        row, col = 0, 0
        max_cols = 2
        
        for entry_id, entry_data in entries.items():
            item_frame = self.create_list_item_frame(entry_id, entry_data)

            self.scroll_layout.addWidget(item_frame, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        self.scroll_layout.setRowStretch(row + 1, 1)
        for c in range(max_cols):
            self.scroll_layout.setColumnStretch(c, 1)
    
    # --- Sort Assist Methods --- #

    def get_pinyin(self, text):
        """Get pinyin letter for sorting"""

        if not text or not HAS_PINYIN:
            return text.lower()
        
        try:
            pinyin_list = pinyin(text, style=Style.NORMAL)
            pinyin_key = ''.join([item[0] for item in pinyin_list if item])
            return pinyin_key.lower()
        except Exception:
            return text.lower()

    def get_accuracy_value(self, accuracy_str):
        """Get accuracy for sorting"""

        if accuracy_str == "N/A %" or not accuracy_str:
            return -1  # N/A at last
        
        try:
            if accuracy_str.endswith('%'):
                value = float(accuracy_str[:-1])
                return value
            else:
                return -1
        except (ValueError, TypeError):
            return -1

    def does_entry_contain_tiles(self, entry_data, search_tiles):
        """Check if an entry contains all tiles in search"""

        # Parse search
        search_tile_list = self.parse_hand_tiles_for_search(search_tiles)
        
        # Parse entries' hands again (well, to normalize the rightmost tile)
        entry_hand_text = entry_data['hands']
        entry_tile_list = self.normalize_hand_tiles(entry_hand_text)
        
        # Count num
        search_counter = Counter(search_tile_list)
        entry_counter = Counter(entry_tile_list)
        
        # Check num
        for tile, count in search_counter.items():
            if entry_counter.get(tile, 0) < count:
                return False
        
        return True

    def normalize_hand_tiles(self, hand_text):
        """Normalize hands (remove and insert the rightmost tile; for the above method and search use)"""

        from src.utils.validators import Validator
        return Validator.normalize_hand_tiles(hand_text)

    # --- Entry Creation Methods --- #
    
    def create_item_frame(self, entry_id, entry_data):

        if self.current_layout == "grid":
            frame = self.create_grid_item_frame(entry_id, entry_data)
        else:
            frame = self.create_list_item_frame(entry_id, entry_data)
        
        # Mouse Track, for multi select by dragging mouse
        frame.setMouseTracking(True)
        frame.is_dragging = False
        frame.entry_id = entry_id
        
        return frame
    
    def create_grid_item_frame(self, entry_id, entry_data):
        """Create grid view item frame"""

        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setMinimumWidth(200)
        frame.setMaximumWidth(500)
        frame.setFixedHeight(360)
        frame.entry_id = entry_id  # Store entry ID

        # Format control (for multi select)
        frame.setObjectName("main_frame")
        
        # Set cursor to hand shape, indicating clickable
        frame.setCursor(Qt.PointingHandCursor)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Image area - fixed height
        image_container = QFrame()
        image_container.setFixedHeight(200)
        image_container.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")
        image_layout = QVBoxLayout()
        image_layout.setAlignment(Qt.AlignCenter)
        
        image_path = self.data_manager.get_image_path(entry_id)
        if image_path and os.path.exists(image_path):
            image_container.setStyleSheet("background-color: #f5f5f5;")
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                image_label = QLabel()
                scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                # Store reference for potential cleanup
                image_label._original_pixmap = scaled_pixmap
                image_layout.addWidget(image_label)
        else:
            image_container.setStyleSheet("background-color: #f5f5f5;")
            no_image_label = QLabel(Dict.t("library.no_image"))
            no_image_label.setAlignment(Qt.AlignCenter)
            image_layout.addWidget(no_image_label)
        
        image_container.setLayout(image_layout)
        main_layout.addWidget(image_container)
        
        # Title - handle long titles with ellipsis, bold
        title_label = QLabel(entry_data['title'])
        title_label.setWordWrap(True)
        title_label.setToolTip(entry_data['title'])  # Show full title on hover
        title_label.setStyleSheet("font-weight: bold;")
        
        # Use QFontMetrics to ensure title doesn't get too long
        metrics = QFontMetrics(title_label.font())
        elided_text = metrics.elidedText(entry_data['title'], Qt.ElideRight, 320)
        title_label.setText(elided_text)
        
        main_layout.addWidget(title_label)
        
        # Metadata
        meta_text = self.get_translated_metadata(entry_data)
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #666;")
        main_layout.addWidget(meta_label)
        
        # Hand display
        hands_frame = QFrame()
        hands_layout = QHBoxLayout()
        hands_layout.setSpacing(0)
        hands_layout.setAlignment(Qt.AlignLeft)
        hands_layout.setContentsMargins(0, 0, 0, 0)
        
        tiles = self.parse_hand_tiles(entry_data['hands'])
        tile_size = 32

        # Apply special hand display logic
        self.display_hand_tiles(hands_layout, tiles, tile_size)
        
        hands_frame.setLayout(hands_layout)
        main_layout.addWidget(hands_frame)
        
        # main_layout.addStretch()
        frame.setLayout(main_layout)
        apply_font_to_widgets(frame.findChildren(QLabel))

        # Set hover effect
        frame.setStyleSheet("""
            #main_frame {
                border: 1px solid #000000;
            }
            #main_frame:hover {
                border: 1px solid #0078d4;
                background-color: #f8fbff;
            }
        """)
        
        # Connect click event
        # frame.mousePressEvent = lambda event, eid=entry_id, w=frame: self.on_entry_clicked(eid, w)
        
        self.setup_drag_selection(frame)
        return frame
    
    def create_list_item_frame(self, entry_id, entry_data):
        """Create list view item frame"""

        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setFixedHeight(108)
        frame.entry_id = entry_id

        # Format control (for multi select)
        frame.setObjectName("main_frame")

        # Set expandable
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set cursor to hand shape, indicating clickable
        frame.setCursor(Qt.PointingHandCursor)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Text information area
        text_container = QWidget()
        text_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title and metadata row
        title_meta_layout = QHBoxLayout()
        title_meta_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(entry_data['title'])
        title_label.setStyleSheet("font-weight: bold;")
        title_label.setToolTip(entry_data['title'])
        
        metrics = QFontMetrics(title_label.font())
        elided_text = metrics.elidedText(entry_data['title'], Qt.ElideRight, 350)
        title_label.setText(elided_text)
        
        title_meta_layout.addWidget(title_label)
        title_meta_layout.addStretch()
        
        # Metadata
        meta_text = self.get_translated_metadata(entry_data)
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #666;")
        title_meta_layout.addWidget(meta_label)
        
        text_layout.addLayout(title_meta_layout)
        
        # Hand display
        hands_frame = QFrame()
        hands_layout = QHBoxLayout()
        hands_layout.setSpacing(1)
        hands_layout.setAlignment(Qt.AlignLeft)
        hands_layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            tiles = self.parse_hand_tiles(entry_data['hands'])
            tile_size = 42
            
            # Apply special hand display logic
            self.display_hand_tiles(hands_layout, tiles, tile_size)
                
        except Exception as e:
            error_label = QLabel("Hand error")
            hands_layout.addWidget(error_label)
        
        hands_frame.setLayout(hands_layout)
        text_layout.addWidget(hands_frame)
        
        text_layout.addStretch()
        text_container.setLayout(text_layout)
        main_layout.addWidget(text_container, 1)  # Set stretch factor to 1 for adaptive text area
        
        frame.setLayout(main_layout)
        apply_font_to_widgets(frame.findChildren(QLabel))
        
        # Set hover effect
        frame.setStyleSheet("""
            #main_frame {
                border: 1px solid #000000;
            }
            #main_frame:hover {
                border: 1px solid #0078d4;
                background-color: #f8fbff;
            }
        """)

        # Connect click event
        # frame.mousePressEvent = lambda event, eid=entry_id, w=frame: self.on_entry_clicked(eid, w)
        
        self.setup_drag_selection(frame)

        return frame
    
    # --- Hand Tile Display Methods --- #
    
    def parse_hand_tiles(self, hand_text):
        """Parse hand text into tile list, handle special hand count display logic"""

        from src.utils.validators import Validator
        return Validator.parse_hand_tiles_for_display(hand_text)
    
    def parse_hand_tiles_for_search(self, hand_text):
        """For search only"""

        from src.utils.validators import Validator
        return Validator._parse_tiles_from_string(hand_text)

    def display_hand_tiles(self, hands_layout, tiles, tile_size):
        """Display hand tiles, handle size & spacing"""

        total_tiles = len(tiles)
        
        if total_tiles in [2, 5, 8, 11, 14] and total_tiles > 1:
            # Special display: sorted tiles in front, last tile displayed separately (with spacing)
            main_tiles = tiles[:-1]
            last_tile = tiles[-1]
            
            # Display main tiles (already sorted by parse)
            for tile in main_tiles:
                tile_label = self.create_tile_label(tile, tile_size)
                hands_layout.addWidget(tile_label)
            
            # Add spacing
            spacer = QLabel()
            spacer.setFixedWidth(20 if tile_size == 32 else 38)
            hands_layout.addWidget(spacer)
            
            # Display last tile
            last_tile_label = self.create_tile_label(last_tile, tile_size)
            hands_layout.addWidget(last_tile_label)
        else:
            # Normal display of all tiles (already sorted by parse)
            for tile in tiles:
                tile_label = self.create_tile_label(tile, tile_size)
                hands_layout.addWidget(tile_label)
    
    def create_tile_label(self, tile, tile_size):
        """Create single tile label, handle size"""

        tile_label = QLabel()
        tile_filename = f"{tile}.png"
        tile_path = os.path.join("src", "assets", "tiles", tile_filename)
        
        if os.path.exists(tile_path):
            pixmap = QPixmap(tile_path)
            if not pixmap.isNull():
                # Scale the pixmap and set it
                scaled_pixmap = pixmap.scaled(tile_size-11, tile_size+5, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                tile_label.setPixmap(scaled_pixmap)
                # Store reference for potential cleanup
                tile_label._original_pixmap = scaled_pixmap
        else:
            tile_label.setText(tile)
            tile_label.setStyleSheet("border: 1px solid #ccc; padding: 2px;")
            tile_label.setAlignment(Qt.AlignCenter)
        
        tile_label.setFixedSize(tile_size-11, tile_size+5)
        return tile_label
    
    # --- Layout and Filter Methods --- #
    
    def change_layout(self, layout_name):
        """Switch layout view """

        # Exit from batch selection mode
        if self.selection_mode:
            self.reset_selection_mode()
            
        if layout_name == Dict.t("library.grid_view"):
            self.current_layout = "grid"
        else:
            self.current_layout = "list"
        self.apply_filters()
    
    def search_items(self, search_text):
        """Text search method removed..."""

        pass
    
    # --- UI Update Methods --- #
    
    def showEvent(self, event):
        """Called when the page becomes visible to refresh page"""

        super().showEvent(event)
        self.reset_selection_mode()
        self.load_library()
        self.apply_font()

    def apply_font(self):

        widgets = []
        
        # Toolbar components
        toolbar_widgets = self.findChildren((QLabel, QComboBox, QLineEdit, QPushButton))
        widgets.extend(toolbar_widgets)
        
        apply_font_to_widgets(widgets)

    def get_translated_metadata(self, entry_data):
        """Get translated metadata"""

        source_key = entry_data['source']
    
        source_display = Dict.t(source_key)
        wind_display = Dict.t(entry_data.get('wind', ''))
        
        # Format: player wind game-honba-turn
        players_key = entry_data.get('players', '')
        player_display = ""
        if players_key in ['players.four', 'players.three']:
            player_number = players_key.split('.')[-1]  # Get 'four' or 'three'
            number_map = {'four': '4', 'three': '3'}
            player_display = number_map.get(player_number, '') + " "

        game_info = f"{player_display}{wind_display} {entry_data.get('game', '')}-{entry_data.get('honba', '')}-{entry_data.get('turn', '')}"
        
        meta_parts = [source_display, game_info]
        if entry_data.get('difficulty', 0) != 0:
            meta_parts.append(f"★{entry_data['difficulty']}")
        
        return " | ".join(meta_parts)
    
    def show_confirmation(self, title, message, need_red=False, need_blue=False):
        """Second confirm dialog; need red"""
        
        msg_box = StyledMessageBox.question(self, title, message, confirm_red=need_red, confirm_blue=need_blue)
        result = msg_box.exec_()
        return result == QMessageBox.Yes