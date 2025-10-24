import json
import os
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QFont

class SettingsManager(QObject):

	settings_changed = pyqtSignal(dict)

	def __init__(self, path: str = "settings.json"):

		super().__init__()
		if path:
			save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saves")
			os.makedirs(save_dir, exist_ok=True)
			self._path = os.path.join(save_dir, "settings.json")
			# print(f"Settings path: {self._path}")
		self._settings = {
            "language": "en",
            "font_size": 12,
			"career_stats": True,
			"timer": False,
			"endless": False
        }
		self.load()

	def load(self):

		if os.path.exists(self._path):
			try:
				with open(self._path, "r", encoding="utf-8") as f:
					data = json.load(f)
					self._settings.update(data)
			except Exception:
				pass

	def save(self):

		try:
			with open(self._path, "w", encoding="utf-8") as f:
				json.dump(self._settings, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def get(self, key: str, default=None):

		return self._settings.get(key, default)

	def set_many(self, updates: dict):

		self._settings.update(updates)
		self.save()
		self.settings_changed.emit(self._settings.copy())

	def apply_to_app(self, app):

		'''lang = self.get("language", "en")'''
		family = "Microsoft YaHei"
		size = int(self.get("font_size", 12))
		font = QFont(family, size)
		app.setFont(font)