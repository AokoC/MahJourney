from PyQt5.QtWidgets import QMessageBox, QPushButton, QProxyStyle, QApplication
from PyQt5.QtCore import Qt
from src.utils.i18n import Dict

class MessageBoxStyle(QProxyStyle):
    
    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == self.SH_DialogButtonLayout:
            # 1: MacLayout
            return 1
        return super().styleHint(hint, option, widget, returnData)

class StyledMessageBox(QMessageBox):

    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.setStyle(MessageBoxStyle())

        self.setStyleSheet("""
            QPushButton { 
                padding: 8px 16px;
                min-width: 20px;
            }
        """)
        
        '''self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint & ~Qt.WindowContextHelpButtonHint)'''
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        '''self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)'''
    
    @classmethod
    def create(cls, parent, title, text, icon=QMessageBox.Information):

        msg = cls(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        return msg
    
    @classmethod
    def warning(cls, parent, title, text):

        msg = cls.create(parent, title, text, QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText(Dict.t("common.confirm"))
        return msg
    
    @classmethod
    def information(cls, parent, title, text):
        
        msg = cls.create(parent, title, text, QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText(Dict.t("common.confirm"))
        return msg
    
    @classmethod
    def critical(cls, parent, title, text):

        msg = cls.create(parent, title, text, QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText(Dict.t("common.confirm"))
        return msg
    
    @classmethod
    def question(cls, parent, title, text, confirm_red=False, confirm_blue=False):

        msg = cls.create(parent, title, text, QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msg.button(QMessageBox.No).setText(Dict.t("common.cancel"))
        msg.button(QMessageBox.Yes).setText(Dict.t("common.confirm"))
        
        if confirm_red:
            confirm_btn = msg.button(QMessageBox.Yes)
            confirm_btn.setStyleSheet("""
                QPushButton {
                    padding: 7px 16px;
                    min-width: 20px;
                    background-color: #c42b1c;
                    color: white;
                    border: 1px solid #3c0808;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #b71c1c;
                }
            """)
        if confirm_blue:
            confirm_btn = msg.button(QMessageBox.Yes)
            confirm_btn.setStyleSheet("""
                QPushButton {
                    padding: 7px 16px;
                    min-width: 20px;
                    background-color: #1976d2;
                    color: white;
                    border: 1px solid #0d47a1;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
        return msg