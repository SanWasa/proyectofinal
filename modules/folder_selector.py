# vault_manager.py
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QFileDialog, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QSettings

class FolderManager:
    def __init__(self, app_name="MiAppNotas", org_name="MiProyecto"):
        self.settings = QSettings(org_name, app_name)

    def get_current_vault(self) -> str:
        vault = self.settings.value("current_vault", None)
        if vault and os.path.exists(vault):
            return vault
        return None

    def set_vault(self, path: str):
        
        if os.path.exists(path):
            self.settings.setValue("current_vault", path)

    def clear_vault(self):
        
        self.settings.remove("current_vault")

class FolderSelectorDialog(QDialog):
    def __init__(self, parent=None, current_vault=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor de Bóvedas")
        self.resize(450, 220)
        self.setModal(True)

        self.selected_vault = current_vault
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Título descriptivo
        lbl_title = QLabel("<h2>Selecciona una Bóveda de Notas</h2>")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        # Estado actual
        ruta_texto = self.selected_vault if self.selected_vault else "Ninguna bóveda seleccionada"
        self.lbl_path = QLabel(f"<b>Ubicación actual:</b><br>{ruta_texto}")
        self.lbl_path.setWordWrap(True)
        layout.addWidget(self.lbl_path)

        # Botones de acción
        btn_layout = QHBoxLayout()

        btn_browse = QPushButton("Abrir carpeta existente...")
        btn_browse.clicked.connect(self.browse_folder)

        btn_confirm = QPushButton("Abrir Bóveda")
        btn_confirm.setStyleSheet("font-weight: bold;")
        btn_confirm.clicked.connect(self.confirm_selection)

        btn_layout.addWidget(btn_browse)
        btn_layout.addWidget(btn_confirm)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def browse_folder(self):
        dir_inicial = self.selected_vault if self.selected_vault else os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Bóveda",
            dir_inicial
        )

        if folder:
            self.selected_vault = folder
            self.lbl_path.setText(f"<b>Ubicación actual:</b><br>{self.selected_vault}")

    def confirm_selection(self):
        if self.selected_vault and os.path.exists(self.selected_vault):
            self.accept()
        else:
            QMessageBox.warning(
                self, 
                "Error", 
                "Por favor selecciona una carpeta válida antes de continuar."
            )