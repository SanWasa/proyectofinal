import os
import json
from PyQt5.QtWidgets import (
    QPushButton, QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QFileDialog, QLabel
)
from PyQt5.QtCore import pyqtSignal, QPoint

DARK_THEME_STYLE = """
/* Botón principal estilo Obsidian (abajo) */
QPushButton#vaultButton {
    background-color: #262626;
    color: #dcddde;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#vaultButton:hover {
    background-color: #313131;
}

/* Menú emergente */
QMenu#vaultMenu {
    background-color: #1e1e1e;
    color: #dcddde;
    border: 1px solid #333333;
    border-radius: 10px;
    padding: 6px;
}

QMenu#vaultMenu::item {
    background-color: transparent;
    padding: 8px 16px;
    border-radius: 6px;
    margin: 2px 0px;
    font-size: 13px;
}

QMenu#vaultMenu::item:selected {
    background-color: #2a2a2a;
    color: #ffffff;
}

QMenu#vaultMenu::separator {
    height: 1px;
    background-color: #333333;
    margin: 6px 4px;
}
"""

class VaultManagerDialog(QDialog):
    """Diálogo para agregar o gestionar carpetas."""
    def __init__(self, folders, parent=None):
        super().__init__(parent)
        self.folders = folders
        self.setWindowTitle("Administrar bóvedas")
        self.resize(380, 220)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: #262626; border-radius: 6px; border: 1px solid #333;")
        self.update_list()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Añadir carpeta")
        btn_add.setStyleSheet("background-color: #2b2b2b; color: white; padding: 6px; border-radius: 4px;")
        btn_add.clicked.connect(self.add_folder)
        btn_layout.addWidget(btn_add)

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet("background-color: #2b2b2b; color: white; padding: 6px; border-radius: 4px;")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def update_list(self):
        self.list_widget.clear()
        for f in self.folders:
            self.list_widget.addItem(f)

    def add_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta para Bóveda")
        if path and path not in self.folders:
            self.folders.append(path)
            self.update_list()


class VaultSelectorButton(QPushButton):
    """Botón que despliega un menú flotante hacia arriba."""
    vault_changed = pyqtSignal(str)

    def __init__(self, config_file="vaults.json", parent=None):
        super().__init__(parent)
        self.setObjectName("vaultButton")
        self.config_file = config_file
        self.folders = []
        self.current_folder = ""

        self.load_folders()

        # Menú flotante personalizado (sin asignárselo directamente con setMenu para controlar su posición)
        self.menu_vaults = QMenu(self)
        self.menu_vaults.setObjectName("vaultMenu")

        self.setStyleSheet(DARK_THEME_STYLE)
        
        # Al hacer clic, mostramos el menú posicionado arriba
        self.clicked.connect(self.show_popup_menu)

        self.rebuild_menu()

    def load_folders(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.folders = json.load(f)
            except Exception:
                self.folders = []
        
        if self.folders and not self.current_folder:
            self.current_folder = self.folders[0]

    def save_folders(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.folders, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar carpetas: {e}")

    def rebuild_menu(self):
        self.menu_vaults.clear()

        # Texto del botón con el icono doble flecha (↕) a la izquierda
        if self.current_folder:
            display_name = os.path.basename(self.current_folder) or self.current_folder
            self.setText(f"  ↕   {display_name}")
        else:
            self.setText("  ↕   Seleccionar bóveda")

        # Opciones de carpetas
        for folder in self.folders:
            folder_name = os.path.basename(folder) or folder
            
            # Formato de texto: Alinea el check (✓) a la derecha si es la bóveda activa
            if folder == self.current_folder:
                # Usamos tabulaciones/espacios para separar el check como en la imagen
                action_text = f"{folder_name}\t✓"
            else:
                action_text = folder_name

            action = QAction(action_text, self)
            action.triggered.connect(lambda checked, f=folder: self.select_vault(f))
            self.menu_vaults.addAction(action)

        self.menu_vaults.addSeparator()

        # Opción final
        manage_action = QAction("🗁  Administrar bóvedas...", self)
        manage_action.triggered.connect(self.open_manager)
        self.menu_vaults.addAction(manage_action)

    def show_popup_menu(self):
        """Calcula la posición exacta para desplegar el menú HACIA ARRIBA."""
        self.rebuild_menu()
        
        # Ajuste para posicionarlo sobre el botón (hacia arriba)
        menu_height = self.menu_vaults.sizeHint().height()
        button_pos = self.mapToGlobal(QPoint(0, 0))
        
        # Desplazar la coordenada Y hacia arriba la altura del menú
        popup_pos = QPoint(button_pos.x(), button_pos.y() - menu_height - 4)
        
        self.menu_vaults.exec_(popup_pos)

    def select_vault(self, folder_path):
        self.current_folder = folder_path
        self.rebuild_menu()
        self.vault_changed.emit(self.current_folder)

    def open_manager(self):
        dialog = VaultManagerDialog(self.folders, parent=self)
        if dialog.exec_():
            self.folders = dialog.folders
            self.save_folders()
            if self.folders and self.current_folder not in self.folders:
                self.current_folder = self.folders[0]
            self.rebuild_menu()