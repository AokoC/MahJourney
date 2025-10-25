import os
from PyQt5.QtWidgets import (   QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QFrame, QScrollArea, QWidget, QMessageBox,
                                QApplication, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap, QFont
from collections import Counter

from src.utils.i18n import Dict
from src.utils.format_applier import apply_font_to_widgets
from src.utils.path_finder import get_resource_path

class TileSelector(QDialog):

    selection_completed = pyqtSignal(str)
    
    def __init__(self, parent=None, mode="hands", current_selection="", hands="", dora="", answer_action="None", is_three_player=False):

        super().__init__(parent)
        self.mode = mode  # "hands", "answer", or "dora", or "search"
        self.current_tiles = self._parse_current_selection(current_selection)
        self.max_tiles = self._get_max_tiles()
        self.tile_limits = self._get_tile_limits()
        
        # 3P mode flag
        self.is_three_player = is_three_player
        
        # Remove question mark button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Record hands / dora, for [answer & dora] / hands: inputted hands / dora
        self.hands_tiles = self._parse_current_selection(hands) if hands else []
        self.dora_tiles = self._parse_current_selection(dora) if dora else []

        # Record last operation for hands: seperate display
        if self.current_tiles and self.mode == "hands" and len(self.current_tiles) in [2, 5, 8, 11, 14]:
            self.last_operation = "add"
        else:
            self.last_operation = None

        # Define valid hands: Enable OK
        self.valid_hand_counts = [0, 1, 2, 4, 5, 7, 8, 10, 11, 13, 14]

        self.answer_action = answer_action
        self.hands_for_validation = hands
        
        self.init_ui()
        self.update_display()

    def init_ui(self):

        if self.mode == "hands":
            self.setWindowTitle(Dict.t("tile_selector.hands.title"))
        elif self.mode == "answer":
            self.setWindowTitle(Dict.t("tile_selector.answer.title"))
        elif self.mode == "dora":
            self.setWindowTitle(Dict.t("tile_selector.dora.title"))
        elif self.mode == "search":
            self.setWindowTitle(Dict.t("tile_selector.search.title"))
        else:
            self.setWindowTitle(Dict.t("tile_selector.title"))

        self.setModal(True)
        # self.setFixedSize(760, 500)
        
        layout = QVBoxLayout()
        # layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Available tiles section
        available_frame = QFrame()
        available_layout = QVBoxLayout()
        # available_layout.setAlignment(Qt.AlignCenter)
        available_layout.setSpacing(0)
        
        '''available_label = QLabel(Dict.t("tile_selector.available_tiles"))
        available_layout.addWidget(available_label)'''
        
        # Create scroll area for available tiles
        scroll_area = QScrollArea()
        scroll_area.setFixedSize(700, 300)
        # available_frame.setFixedSize(730, 400)
        # scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.tiles_layout = QVBoxLayout(scroll_widget)
        # self.tiles_layout.setAlignment(Qt.AlignCenter)
        
        # Create rows for different suits
        self.create_tile_row('m', "1234056789")
        self.create_tile_row('p', "1234056789") 
        self.create_tile_row('s', "1234056789")
        self.create_tile_row('z', "1234567")
        
        scroll_area.setWidget(scroll_widget)
        available_layout.addWidget(scroll_area)
        available_frame.setLayout(available_layout)
        layout.addWidget(available_frame)
        
        # Selected tiles section
        selected_frame = QFrame()
        selected_layout = QVBoxLayout()
        
        '''selected_label = QLabel(Dict.t("tile_selector.selected_tiles"))
        selected_layout.addWidget(selected_label)'''
        
        # Selected tiles display
        self.selected_container = QFrame()
        self.selected_container.setFixedHeight(80)
        self.selected_layout = QHBoxLayout(self.selected_container)
        self.selected_layout.setAlignment(Qt.AlignLeft)
        self.selected_layout.setSpacing(0)
        selected_layout.addWidget(self.selected_container)
        
        selected_frame.setLayout(selected_layout)
        layout.addWidget(selected_frame)
        
        # Button
        button_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton(Dict.t("action.reset"))
        self.btn_reset.setStyleSheet("QPushButton{padding:8;}")
        self.btn_reset.clicked.connect(self.reset_selection)
        button_layout.addWidget(self.btn_reset)
        button_layout.addStretch()
        
        self.btn_ok = QPushButton(Dict.t("common.ok"))
        self.btn_ok.setStyleSheet("QPushButton{padding:8;}")
        self.btn_ok.clicked.connect(self.accept_selection)
        button_layout.addWidget(self.btn_ok)
        
        '''self.btn_cancel = QPushButton(Dict.t("common.cancel"))
        self.btn_cancel.setStyleSheet("QPushButton{padding:8;}")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)'''
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Apply font settings
        self.apply_font()

    def showEvent(self, event: QEvent):
        super().showEvent(event)
        self.update_available_tiles_state()
        self.setFixedSize(self.width(), self.height())

    # --- Tiles related Algorithms --- #

    def _get_max_tiles(self):
        """Return upper limit of tile count"""

        if self.mode == "hands" or self.mode == "search":
            return 14
        elif self.mode == "answer":
            return 3
        elif self.mode == "dora":
            return 5
        return 14
    
    def _get_tile_limits(self):
        """Return upper limit of each tile"""

        limits = {}
        # 4 for most tiles, 1 for 0mps, 3 for 5mps
        for suit in ['m', 'p', 's']:
            for num in '123456789':
                limits[num + suit] = 4
            limits['0' + suit] = 1
            limits['5' + suit] = 3
        
        for suit in ['z']:
            for num in '1234567':
                limits[num + suit] = 4
        
        if self.mode == "answer":
            # Answer mode, all tiles only can select once
            for tile in limits:
                limits[tile] = 1
        
        return limits
    
    def _parse_current_selection(self, selection):
        """Parse current selection string into list of tiles"""

        if not selection:
            return []
        
        tiles = []
        current_numbers = ""

        if self.mode == "hands" and len(selection.replace('m', '').replace('p', '').replace('s', '').replace('z', '')) in [2, 5, 8, 11, 14]:
            if len(selection) >= 2 and selection[-1] in 'mpsz' and selection[-2] in '0123456789':
                last_tile = selection[-2] + selection[-1]
                main_part = selection[:-2]

                current_numbers = ""
                for char in main_part:
                    if char in 'mpsz':
                        if current_numbers:
                            for num in current_numbers:
                                tiles.append(num + char)
                            current_numbers = ""
                    elif char in '0123456789':
                        current_numbers += char

                tiles.append(last_tile)
                return tiles
        
        for char in selection:
            if char in 'mpsz':
                if current_numbers:
                    for num in current_numbers:
                        tiles.append(num + char)
                    current_numbers = ""
            elif char in '0123456789':
                current_numbers += char
        
        return tiles
    
    def _tiles_to_string(self, tiles):
        """Return string of the tiles selected"""

        if not tiles:
            return ""
        
        # For answer/dora mode, no sorting is ok
        if self.mode == "answer" or self.mode == "dora":
            result = ""
            current_suit = None
            current_numbers = ""

            for tile in tiles:
                num = tile[0]
                suit = tile[1]

                if current_suit and suit != current_suit:
                    result += current_numbers + current_suit
                    current_numbers = ""
                
                current_suit = suit
                current_numbers += num

            if current_suit:
                result += current_numbers + current_suit

            # print(result)
            return result
        
        # For hands mode with special count, handle the last tile separately
        if self.mode == "hands" and len(tiles) in [2, 5, 8, 11, 14]:
            # Separate the last tile from the rest
            main_tiles = tiles[:-1]
            last_tile = tiles[-1]
            
            # Group main tiles by suit (sorted)
            suits = {'m': [], 'p': [], 's': [], 'z': []}
            for tile in main_tiles:
                num = tile[0]
                suit = tile[1]
                suits[suit].append(num)

            result = ""
            for suit in ['m', 'p', 's', 'z']:
                if suits[suit]:
                    # Sort numbers
                    suits[suit].sort(key=lambda x: 4.5 if x == '0' else float(x))
                    result += ''.join(suits[suit]) + suit
            
            # Append the last tile separately
            result += last_tile

            # print(result)
            return result
        
        else:
            # Normal grouping for other cases
            suits = {'m': [], 'p': [], 's': [], 'z': []}
            for tile in tiles:
                num = tile[0]
                suit = tile[1]
                suits[suit].append(num)
            
            result = ""
            for suit in ['m', 'p', 's', 'z']:
                if suits[suit]:
                    # Sort numbers
                    suits[suit].sort(key=lambda x: 4.5 if x == '0' else float(x))
                    result += ''.join(suits[suit]) + suit
            
            # print(result)
            return result
    
    def _sort_tiles(self, tiles):
        """Sort tiles and handle 0mps"""

        if self.mode != "hands" and self.mode != "search":
            return tiles.copy()
        
        # Group tiles by suit
        suits = {'m': [], 'p': [], 's': [], 'z': []}
        for tile in tiles:
            num = tile[0]
            suit = tile[1]
            suits[suit].append(num)
        
        # Sort numbers within each suit
        for suit in ['m', 'p', 's', 'z']:
            suits[suit].sort(key=lambda x:4.5 if x=='0' else float(x))
        
        # Reconstruct the sorted tile list
        sorted_tiles = []
        for suit in ['m', 'p', 's', 'z']:
            for num in suits[suit]:
                sorted_tiles.append(num + suit)
        
        return sorted_tiles
    
    def _find_insert_position(self, tile, sorted_tiles):
        """Find the correct position to insert a tile in a sorted list"""

        if self.mode != "hands" and self.mode != "search":
            return len(sorted_tiles)
        
        tile_num = tile[0]
        tile_suit = tile[1]
        
        # Define suit order
        suit_order = {'m': 0, 'p': 1, 's': 2, 'z': 3}

        tile_value = 4.5 if tile_num == '0' else float(tile_num)
        
        for i, existing_tile in enumerate(sorted_tiles):
            existing_num = existing_tile[0]
            existing_suit = existing_tile[1]
            
            # Compare suits first
            if suit_order[tile_suit] < suit_order[existing_suit]:
                return i
            elif suit_order[tile_suit] > suit_order[existing_suit]:
                continue
            
            # Same suit, compare numbers
            existing_value = 4.5 if existing_num == '0' else float(existing_num)
            if tile_value < existing_value:
                return i
        
        # If no position found, insert at the end
        return len(sorted_tiles)
    
    # --- Tiles related Edit --- #

    def create_tile_row(self, suit, numbers):
        """Create a row of clickable tiles for a suit"""

        row_frame = QFrame()
        row_layout = QHBoxLayout(row_frame)
        row_layout.setAlignment(Qt.AlignCenter)
        row_layout.setSpacing(10) # space between tiles
        row_layout.setContentsMargins(80, 0, 80, 0) # left, top, right, bottom
        
        for num in numbers:
            tile = num + suit
            tile_label = QLabel()
            
            # Load tile image
            tile_filename = f"{tile}.png"
            tile_path = get_resource_path(os.path.join("src", "assets", "tiles", tile_filename))
            
            pixmap = QPixmap(tile_path)
            pixmap = pixmap.scaled(42, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            tile_label.setPixmap(pixmap)
            
            tile_label.setFixedSize(42, 60)
            tile_label.setCursor(Qt.PointingHandCursor)
            tile_label.mousePressEvent = lambda event, t=tile: self.on_tile_click(t)
            tile_label.setProperty("tile", tile)
            
            row_layout.addWidget(tile_label)
        
        #row_layout.addStretch()
        self.tiles_layout.addWidget(row_frame)
    
    def on_tile_click(self, tile):
        """Handle tile click"""

        # Calculate total usage of hands and dora
        total_used_tiles = Counter(self.hands_tiles + self.dora_tiles)
        current_count = self.current_tiles.count(tile)
        total_count = total_used_tiles.get(tile, 0) + current_count

        if self.mode == "answer":
            tile_limit = self.tile_limits.get(tile, 4)
            if current_count >= tile_limit:
                return
        
        # Check global tile limit
        tile_limit = self.tile_limits.get(tile, 4)
        if (total_count >= tile_limit and self.mode != "answer"):
            '''QMessageBox.warning( self, Dict.t("msg.hint"),
                                    Dict.t("tile_selector.tile_limit").format(tile, tile_limit))'''
            return
        
        # Check total limit for this selector
        if len(self.current_tiles) >= self.max_tiles:
            '''QMessageBox.warning( self, Dict.t("msg.hint"), 
                                    Dict.t("tile_selector.max_tiles").format(self.max_tiles))'''
            return

        # This variable relates to the situation of sorting, and the rightmost tile displayed
        self.last_operation = "add"

        # Check if is at 2, 5, 8, 11, 14; for seperate display in update_display
        '''if self.mode == "hands":
            new_count = len(self.current_tiles) + 1
            if new_count in [2, 5, 8, 11, 14]:
                # Append to the end
                self.current_tiles.append(tile)
            else:
                # No append, insert in sorted order
                sorted_tiles = self._sort_tiles(self.current_tiles)
                insert_pos = self._find_insert_position(tile, sorted_tiles)
                self.current_tiles.insert(insert_pos, tile)
        else:
            # For other modes, just append
            self.current_tiles.append(tile)'''
        
        new_count = len(self.current_tiles) + 1
    
        if self.mode == "hands" and new_count in [2, 5, 8, 11, 14]:
            self.current_tiles.append(tile)
        else:
            sorted_tiles = self._sort_tiles(self.current_tiles)
            insert_pos = self._find_insert_position(tile, sorted_tiles)
            self.current_tiles.insert(insert_pos, tile)
        
        self.update_display()
        self.update_ok_button_state()
    
    def remove_tile(self, tile_index):
        """Remove tile from selection (on click)"""

        '''self.last_operation = "remove"
        if 0 <= tile_index < len(self.current_tiles):
            self.current_tiles.pop(tile_index)
            self.update_display()

        self.update_ok_button_state()'''

        '''self.last_operation = "remove"
    
        if 0 <= tile_index < len(self.current_tiles):
            removed_tile = self.current_tiles.pop(tile_index)
            
            if (self.mode == "hands" and 
                len(self.current_tiles) in [2, 5, 8, 11, 14]):
                pass
                
            self.update_display()
            self.update_ok_button_state()'''
        
        self.last_operation = "remove"
    
        if 0 <= tile_index < len(self.current_tiles):
            removed_tile = self.current_tiles.pop(tile_index)
            
            if (self.mode == "hands" and 
                len(self.current_tiles) in [2, 5, 8, 11, 14]):
                
                if len(self.current_tiles) > 0:
                    sorted_tiles = self._sort_tiles(self.current_tiles)
                    last_tile = sorted_tiles[-1]
                    sorted_tiles = sorted_tiles[:-1] + [last_tile]
                    
                    self.current_tiles = sorted_tiles
            
            self.update_display()
            self.update_ok_button_state()

    '''def add_tile_to_display(self, tile, index):
        # Answer and dora mode, add single tile only

        tile_frame = QFrame()
        tile_frame.setFixedSize(45, 60)
        tile_layout = QVBoxLayout(tile_frame)
        tile_layout.setContentsMargins(0, 0, 0, 0)
        tile_layout.setSpacing(0)
        
        tile_label = QLabel()
        
        tile_filename = f"{tile}.png"
        tile_path = get_resource_path(os.path.join("src", "assets", "tiles", tile_filename))
        
        pixmap = QPixmap(tile_path)
        pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        tile_label.setPixmap(pixmap)
        tile_label.setFixedSize(45, 60)
        
        tile_label.mousePressEvent = lambda event, idx=index: self.remove_tile(idx)
        tile_label.setCursor(Qt.PointingHandCursor)
        
        tile_layout.addWidget(tile_label)
        self.selected_layout.addWidget(tile_frame)'''

    def add_placeholder_tile(self, index):
        """Add the tile back (for dora, answer)"""

        tile_frame = QFrame()
        tile_frame.setFixedSize(45, 60)
        tile_layout = QVBoxLayout(tile_frame)
        tile_layout.setContentsMargins(0, 0, 0, 0)
        tile_layout.setSpacing(0)

        tile_label = QLabel()

        back_path = get_resource_path(os.path.join("src", "assets", "tiles", "back.png"))

        pixmap = QPixmap(back_path)
        pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        tile_label.setPixmap(pixmap)
        tile_label.setFixedSize(45, 60)

        tile_label.setCursor(Qt.ArrowCursor)
        
        tile_layout.addWidget(tile_label)
        self.selected_layout.addWidget(tile_frame)

    # --- Tiles related Display Update ---#

    def update_display(self):
        """Update the selected tiles display"""

        # Clear current display
        for i in reversed(range(self.selected_layout.count())):
            widget = self.selected_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Answer/dora mode, display logic
        if self.mode == "answer" or self.mode == "dora":
            max_choice = 3 if self.mode == "answer" else 5

            for i in range(max_choice):
                if i < len(self.current_tiles):
                    tile = self.current_tiles[i]

                    tile_frame = QFrame()
                    tile_frame.setFixedSize(45, 60)
                    tile_layout = QVBoxLayout(tile_frame)
                    tile_layout.setContentsMargins(0, 0, 0, 0)
                    tile_layout.setSpacing(0)
                    
                    tile_label = QLabel()
                    
                    tile_filename = f"{tile}.png"
                    tile_path = get_resource_path(os.path.join("src", "assets", "tiles", tile_filename))
                    
                    pixmap = QPixmap(tile_path)
                    pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    tile_label.setPixmap(pixmap)
                    tile_label.setFixedSize(45, 60)
                    
                    tile_label.mousePressEvent = lambda event, idx=i: self.remove_tile(idx)
                    tile_label.setCursor(Qt.PointingHandCursor)
                    
                    tile_layout.addWidget(tile_label)
                    self.selected_layout.addWidget(tile_frame)
                else:
                    # Add back tile as placeholder part
                    placeholder_frame = QFrame()
                    placeholder_frame.setFixedSize(45, 60)
                    placeholder_layout = QVBoxLayout(placeholder_frame)
                    placeholder_layout.setContentsMargins(0, 0, 0, 0)
                    placeholder_layout.setSpacing(0)
                    
                    placeholder_label = QLabel()
                    
                    # Load back tile image
                    back_path = get_resource_path(os.path.join("src", "assets", "tiles", "back.png"))
                    pixmap = QPixmap(back_path)
                    pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    placeholder_label.setPixmap(pixmap)
                    placeholder_label.setFixedSize(45, 60)
                    placeholder_label.setCursor(Qt.ArrowCursor)
                    
                    placeholder_layout.addWidget(placeholder_label)
                    self.selected_layout.addWidget(placeholder_frame)
                
                # Add or
                if self.mode == "answer" and i < 2:
                    or_label = QLabel(Dict.t("answer.or"))
                    or_label.setAlignment(Qt.AlignCenter)
                    or_label.setFixedWidth(80)
                    self.selected_layout.addWidget(or_label)

        elif self.mode == "search":
            display_tiles = self._sort_tiles(self.current_tiles)
            
            # Add selected tiles to display
            for i, tile in enumerate(display_tiles):
                tile_frame = QFrame()
                tile_frame.setFixedSize(45, 60)
                tile_layout = QVBoxLayout(tile_frame)
                tile_layout.setContentsMargins(0, 0, 0, 0)
                tile_layout.setSpacing(0)
                
                tile_label = QLabel()
                
                # Load tile image
                tile_filename = f"{tile}.png"
                tile_path = get_resource_path(os.path.join("src", "assets", "tiles", tile_filename))
                
                pixmap = QPixmap(tile_path)
                pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                tile_label.setPixmap(pixmap)
                tile_label.setFixedSize(45, 60)

                # Find the actual index in current_tiles for removal
                try:
                    actual_index = self.current_tiles.index(tile)
                except ValueError:
                    actual_index = i
                
                tile_label.mousePressEvent = lambda event, idx=actual_index: self.remove_tile(idx)
                tile_label.setCursor(Qt.PointingHandCursor)
                
                tile_layout.addWidget(tile_label)
                self.selected_layout.addWidget(tile_frame)

        else: 
            # Hands mode, display logic
            if self.mode == "hands":
                tile_count = len(self.current_tiles)

                if tile_count in [2, 5, 8, 11, 14]:
                    '''if self.last_operation == "add":
                        # Add, need seperate display
                        if tile_count > 1:
                            # Sort all tiles except the last one
                            sorted_tiles = self._sort_tiles(self.current_tiles[:-1])
                            display_tiles = sorted_tiles + [self.current_tiles[-1]]
                        else:
                            display_tiles = self.current_tiles.copy()
                    else:
                        # Remove
                        sorted_tiles = self._sort_tiles(self.current_tiles)
                        display_tiles = sorted_tiles[:-1] + [sorted_tiles[-1]]'''
                    
                    if tile_count > 1:
                        sorted_tiles = self._sort_tiles(self.current_tiles[:-1])
                        display_tiles = sorted_tiles + [self.current_tiles[-1]]
                    else:
                        display_tiles = self.current_tiles.copy()
                else:
                    # Normal case: sort all tiles
                    display_tiles = self._sort_tiles(self.current_tiles)
            else:
                # For other modes, just use current order
                display_tiles = self.current_tiles.copy()
            
            # Add selected tiles to display
            for i, tile in enumerate(display_tiles):
                tile_frame = QFrame()
                tile_frame.setFixedSize(45, 60)
                tile_layout = QVBoxLayout(tile_frame)
                tile_layout.setContentsMargins(0, 0, 0, 0)
                tile_layout.setSpacing(0)
                
                tile_label = QLabel()
                
                # Load tile image
                tile_filename = f"{tile}.png"
                tile_path = get_resource_path(os.path.join("src", "assets", "tiles", tile_filename))
                
                pixmap = QPixmap(tile_path)
                pixmap = pixmap.scaled(45, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                tile_label.setPixmap(pixmap)
                tile_label.setFixedSize(45, 60)

                # Find the actual index in current_tiles for removal
                if (    self.mode == "hands" and 
                        len(self.current_tiles) in [2, 5, 8, 11, 14] and 
                        i == len(display_tiles) - 1):
                    '''# Last tile seperate display
                    if self.last_operation == "add":
                        # Add: Last tile added
                        actual_index = len(self.current_tiles) - 1
                    else:
                        # Remove: Last tile after sort
                        try:
                            actual_index = self.current_tiles.index(tile)
                        except ValueError:
                            actual_index = len(self.current_tiles) - 1'''
                    actual_index = len(self.current_tiles) - 1
                else:
                    # Find the actual index in current_tiles
                    try:
                        actual_index = self.current_tiles.index(tile)
                    except ValueError:
                        actual_index = i
                
                tile_label.mousePressEvent = lambda event, idx=actual_index: self.remove_tile(idx)
                tile_label.setCursor(Qt.PointingHandCursor)
                
                tile_layout.addWidget(tile_label)
                self.selected_layout.addWidget(tile_frame)
                
                # Apply spacing for the last tile in hands mode 2, 5, 8, 11, 14
                if (self.mode == "hands" and 
                    len(self.current_tiles) in [2, 5, 8, 11, 14] and 
                    i == len(display_tiles) - 2):
                    spacer = QFrame()
                    spacer.setFixedWidth(45)
                    self.selected_layout.addWidget(spacer)

        # Update available tiles enabled state
        self.update_available_tiles_state()

        # Update OK button enabled state
        self.update_ok_button_state()
    
    def update_available_tiles_state(self):
        """Define unavailable tiles, and make them transparent and not clickable"""

        '''reached_max = len(self.current_tiles) >= self.max_tiles'''

        '''print(f"DEBUG - Mode: {self.mode}")
        print(f"DEBUG - hands_tiles: {self.hands_tiles}")
        print(f"DEBUG - dora_tiles: {self.dora_tiles}")
        print(f"DEBUG - current_tiles: {self.current_tiles}")
        
        total_used_tiles = Counter(self.hands_tiles + self.dora_tiles)
        print(f"DEBUG - total_used_tiles: {dict(total_used_tiles)}")'''

        total_used_tiles = Counter(self.hands_tiles + self.dora_tiles)

        for row in range(self.tiles_layout.count()):
            row_widget = self.tiles_layout.itemAt(row).widget()

            if row_widget:
                for i in range(row_widget.layout().count()):
                    item = row_widget.layout().itemAt(i)

                    if item and item.widget():
                        widget = item.widget()
                        tile = widget.property("tile")

                        if tile:
                            '''tile_count = self.current_tiles.count(tile)

                            # Answer, dora mode hands check
                            if (self.mode == "answer" or self.mode == "dora") and self.hands_tiles:
                                is_enabled = (tile in self.hands_tiles and
                                            len(self.current_tiles) < self.max_tiles and
                                            tile_count < self.tile_limits.get(tile, 4))

                            # Upper limit check
                            else: 
                                if reached_max: 
                                    is_enabled = False
                                else:
                                    is_enabled = (len(self.current_tiles) < self.max_tiles
                                    and tile_count < self.tile_limits.get(tile, 4))'''

                            # Count current selection in this selector
                            current_count = self.current_tiles.count(tile)
                            # Count total usage from OTHER selectors (hands + dora), excluding current selection.
                            other_usage_count = total_used_tiles.get(tile, 0)
                            # Total usage including current selection
                            total_usage_with_current = other_usage_count + current_count
                            
                            # Get tile limit
                            tile_limit = self.tile_limits.get(tile, 4)
                            
                            # Check if reached max tiles for this selector
                            reached_selector_max = len(self.current_tiles) >= self.max_tiles
                            # Check if reached global tile limit (including current selection)
                            reached_global_limit = total_usage_with_current >= tile_limit
                            
                            # Check 3P mode restriction first
                            is_three_player_disabled = (self.is_three_player and 
                                                       tile[1] == 'm' and 
                                                       tile[0] in '02345678')
                            
                            # For answer mode with hands validation
                            if self.mode == "answer":
                                reached_tile_limit = current_count >= 1
                                in_hands = tile in self.hands_tiles
                                
                                is_enabled = (  not is_three_player_disabled and
                                                in_hands and 
                                                not reached_selector_max and 
                                                not reached_tile_limit)
                            # For other modes
                            else:
                                is_enabled = (  not is_three_player_disabled and
                                                not reached_selector_max and 
                                                not reached_global_limit)

                            '''else:
                                is_enabled = (  not reached_selector_max and 
                                                not reached_global_limit)'''

                            '''# Check if tiles are needed for furo
                            if (is_enabled and self.mode == "answer" and self.answer_action and 
                                self.answer_action in ["chi", "pon", "kan"] and 
                                self.hands_for_validation):
                                
                                from src.utils.validators import Validator
                                required_tiles = Validator.get_required_tiles_for_meld(
                                    self.hands_for_validation, self.answer_action
                                )
                                
                                if tile in required_tiles:
                                    is_enabled = False'''
                            
                            effect = QGraphicsOpacityEffect()
                            effect.setOpacity(0.2 if not is_enabled else 1.0)
                            widget.setGraphicsEffect(effect)
                            
                            widget.setCursor(Qt.ForbiddenCursor if not is_enabled
                            else Qt.PointingHandCursor)
                            
                            # Set Property to define the tile is clickable or not
                            widget.setProperty("enabled", is_enabled)

    def update_ok_button_state(self):
        """Update OK button of window"""

        if self.mode == "hands":
            tile_count = len(self.current_tiles)
            self.btn_ok.setEnabled(tile_count in self.valid_hand_counts)
        else:
            self.btn_ok.setEnabled(True)

    # --- Static methods --- #
    
    @staticmethod
    def parse_tiles_string(tiles_string):
        """Parse tiles, not affected by mode..."""

        if not tiles_string:
            return []
        
        tiles = []
        current_numbers = ""
        
        for char in tiles_string:
            if char in 'mpsz':
                if current_numbers:
                    for num in current_numbers:
                        tiles.append(num + char)
                    current_numbers = ""
            elif char in '0123456789':
                current_numbers += char 
        return tiles

    # --- Return methods --- #

    def reset_selection(self):

        self.current_tiles = []
        self.update_display()

        self.update_ok_button_state()
    
    def accept_selection(self):

        tile_string = self._tiles_to_string(self.current_tiles)
        self.selection_completed.emit(tile_string)
        self.accept()
    
    # --- Font / Lang / UI --- #

    def apply_font(self):

        widgets = [
            self.btn_ok, 
            # self.btn_cancel, 
            self.btn_reset
        ]
        apply_font_to_widgets(widgets)
    
    def retranslate_ui(self):
        
        self.setWindowTitle(Dict.t("tile_selector.title"))
        self.setWindowTitle(Dict.t("tile_selector.hands.title"))
        self.setWindowTitle(Dict.t("tile_selector.answer.title"))
        self.setWindowTitle(Dict.t("tile_selector.dora.title"))
        self.btn_ok.setText(Dict.t("action.ok"))
        # self.btn_cancel.setText(Dict.t("action.cancel"))
        self.btn_reset.setText(Dict.t("action.reset"))