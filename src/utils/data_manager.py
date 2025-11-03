import os
import sys
import json
import shutil
from datetime import datetime
import uuid

class DataManager:
    def __init__(self, base_dir=None):
        """Set save folder/file"""
        # Determine base directory for saves.
        # When frozen by PyInstaller, put saves next to the executable so
        # the folder sits beside the .exe. During development, keep saves
        # under the project root.
        if getattr(sys, 'frozen', False):
            # sys.executable points to the running exe; use its directory.
            base = os.path.dirname(sys.executable)
        else:
            # project root: two levels up from this utils folder
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        saves_dir = os.path.join(base, "saves")
        os.makedirs(saves_dir, exist_ok=True)
        self.images_dir = os.path.join(saves_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        self.data_file = os.path.join(saves_dir, "data.json")
        
        if not os.path.exists(self.data_file):
            self.save_data({})
    
    def save_entry(self, image_path, data):

        try:
            entry_id = str(uuid.uuid4())
            
            # Deal with image
            image_filename = ""
            if image_path and os.path.exists(image_path):

                # Use UUID4 as file name
                file_ext = os.path.splitext(image_path)[1]
                image_filename = f"{entry_id}{file_ext}"
                destination_path = os.path.join(self.images_dir, image_filename)
                shutil.copy2(image_path, destination_path)

            # If image_path is None or "", image_filename is ""
            
            all_data = self.load_all_data()
            
            # Create new entry
            entry_data = data.copy()
            entry_data['image_filename'] = image_filename
            entry_data['id'] = entry_id
            
            # Add to data
            all_data[entry_id] = entry_data
            
            # Save
            return self.save_data(all_data)
            
        except Exception as e:
            # print(f"Save wrong: {e}")
            return False
    
    def load_entries(self):

        return self.load_all_data()
    
    def load_all_data(self):

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_data(self, data):
        """Save data for an entry with certain format"""

        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                f.write('{\n')
                entries = []
                for entry_id, entry_data in data.items():
                    # Format each entry with compact layout
                    entry_lines = []
                    entry_lines.append(f'  "{entry_id}": {{')
                    
                    # Helper function to safely format string values
                    def safe_str(value):
                        if value is None:
                            return '""'
                        # Escape quotes and newlines in string values
                        escaped = str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                        return f'"{escaped}"'
                    
                    # Group related fields on same line
                    entry_lines.append(f'    "create_time": {safe_str(entry_data.get("create_time", ""))}, "title": {safe_str(entry_data.get("title", ""))},')
                    entry_lines.append(f'    "encounter": {entry_data.get("encounter", 0)}, "correct": {entry_data.get("correct", 0)}, "accuracy": {safe_str(entry_data.get("accuracy", "N/A %"))},')
                    entry_lines.append(f'    "source": {safe_str(entry_data.get("source", ""))}, "players": {safe_str(entry_data.get("players", ""))}, "difficulty": {entry_data.get("difficulty", 0)},')
                    entry_lines.append(f'    "wind": {safe_str(entry_data.get("wind", ""))}, "self_wind": {safe_str(entry_data.get("self_wind", ""))}, "game": {safe_str(entry_data.get("game", ""))}, "honba": {safe_str(entry_data.get("honba", ""))}, "turn": {safe_str(entry_data.get("turn", ""))},')
                    entry_lines.append(f'    "dora": {safe_str(entry_data.get("dora", ""))}, "hands": {safe_str(entry_data.get("hands", ""))}, "answer_action": {safe_str(entry_data.get("answer_action", ""))}, "answer_input": {safe_str(entry_data.get("answer_input", ""))},')
                    entry_lines.append(f'    "intro": {safe_str(entry_data.get("intro", ""))}, "notes": {safe_str(entry_data.get("notes", ""))},')
                    entry_lines.append(f'    "image_filename": {safe_str(entry_data.get("image_filename", ""))}, "id": {safe_str(entry_data.get("id", ""))} }}')
                    
                    entries.append('\n'.join(entry_lines))
                
                f.write(',\n'.join(entries))
                f.write('\n}')
            return True
        except Exception as e:
            # print(f"{e}")
            return False
    
    def get_image_path(self, entry_id):
        """Get the image path from files"""

        data = self.load_all_data()
        if entry_id in data:
            image_filename = data[entry_id].get('image_filename')
            if image_filename:
                image_path = os.path.join(self.images_dir, image_filename)
                if os.path.exists(image_path):
                    return image_path
        return None
    
    def load_entry(self, entry_id):
        """Load a single entry by ID"""

        data = self.load_all_data()
        return data.get(entry_id)
    
    def update_entry(self, entry_id, image_path, data):
        """Update an existing entry"""

        try:
            all_data = self.load_all_data()
            if entry_id not in all_data:
                return False
            
            old_image_filename = all_data[entry_id].get('image_filename', '')
            new_image_filename = old_image_filename
            
            # Only when image_path is not None and is Different, update
            if image_path is not None:
                if image_path and os.path.exists(image_path):
                    # Check if is new
                    current_image_path = self.get_image_path(entry_id)
                    if current_image_path != image_path:
                        file_ext = os.path.splitext(image_path)[1]
                        new_image_filename = f"{entry_id}{file_ext}"
                        destination_path = os.path.join(self.images_dir, new_image_filename)
                        shutil.copy2(image_path, destination_path)
                        
                        # Delete old
                        if old_image_filename and old_image_filename != new_image_filename:
                            old_image_path = os.path.join(self.images_dir, old_image_filename)
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                    else:
                        # Keep
                        new_image_filename = old_image_filename
                else:
                    # image_path is "", means clear
                    new_image_filename = ""
                    if old_image_filename:
                        old_image_path = os.path.join(self.images_dir, old_image_filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
            else:
                # Keep
                new_image_filename = old_image_filename
            
            # Update entry data
            entry_data = data.copy()
            entry_data['image_filename'] = new_image_filename
            entry_data['id'] = entry_id
            
            all_data[entry_id] = entry_data
            
            return self.save_data(all_data)
            
        except Exception as e:
            print(f"Update wrong: {e}")
            return False
    
    def delete_entry(self, entry_id):
        """Delete an entry"""

        try:
            data = self.load_all_data()
            if entry_id in data:
                
                # Delete image
                image_path = self.get_image_path(entry_id)
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)
                
                # Delete data
                del data[entry_id]
                self.save_data(data)

                return True
            return False
        except Exception as e:
            # print(f"{e}")
            return False
    
    def load_entry_stats(self, entry_id):
        """Get career stats for an entry"""

        all_data = self.load_all_data()
        if entry_id in all_data:
            return all_data[entry_id].get('career_stats', {'encounter': 0, 'correct': 0})
        return None
    
    '''def save_entry_stats(self, entry_id, stats):
        """Save career stats for an entry"""
        try:
            all_data = self.load_all_data()
            if entry_id in all_data:
                all_data[entry_id]['career_stats'] = stats
                return self.save_data(all_data)
            return False
        except Exception:
            return False'''