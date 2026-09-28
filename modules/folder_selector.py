import os
import json
from PyQt5.QtWidgets import (
    QPushButton, QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QLabel, QWidgetAction
)
from PyQt5.QtCore import pyqtSignal, Qt

class VaultManagerDialog(QDialog):
    """Diálogo secundario para gestionar/añadir carpetas guardadas."""
    def __init__(self, folders, parent=None):
        super().__init__(parent)
        self.folders = folders
        self.setWindowTitle("Administrar Bóvedas")
        self.resize(400, 250)
        
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.update_list()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Añadir Nueva Carpeta")
        btn_add.clicked.connect(self.add_folder)
        btn_layout.addWidget(btn_add)

        btn_close = QPushButton("Cerrar")
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
    """Botón con menú desplegable que simula el selector de bóvedas."""
    vault_changed = pyqtSignal(str)

    def __init__(self, config_file="vaults.json", parent=None):
        super().__init__(parent)
        self.setObjectName("vaultButton")
        self.config_file = config_file
        self.folders = []
        self.current_folder = ""

        # Cargar carpetas persistentes
        self.load_folders()

        # Configurar menú desplegable
        self.menu_vaults = QMenu(self)
        self.setMenu(self.menu_vaults)

        # Aplicar hojas de estilo QSS
        #self.setStyleSheet(DARK_THEME_STYLE)

        # Renderizar opciones del menú
        self.rebuild_menu()

    def load_folders(self):
        """Carga las rutas guardadas desde el archivo JSON."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.folders = json.load(f)
            except Exception:
                self.folders = []
        
        if self.folders and not self.current_folder:
            self.current_folder = self.folders[0]

    def save_folders(self):
        """Guarda la lista de carpetas en el archivo JSON."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.folders, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar carpetas: {e}")

    def rebuild_menu(self):
        """Reconstruye dinámicamente las opciones del menú desplegable."""
        self.menu_vaults.clear()

        if self.current_folder:
            display_name = os.path.basename(self.current_folder) or self.current_folder
            self.setText(f"  {display_name}   ▾")
        else:
            self.setText("  Seleccionar Bóveda   ▾")

        # Agregar carpetas registradas al menú
        for folder in self.folders:
            folder_name = os.path.basename(folder) or folder
            
            # Añadir indicador visual (✓) a la opción actualmente activa
            if folder == self.current_folder:
                action_text = f"{folder_name}   ✓"
            else:
                action_text = folder_name

            action = QAction(action_text, self)
            action.triggered.connect(lambda checked, f=folder: self.select_vault(f))
            self.menu_vaults.addAction(action)

        # Separador horizontal como en la imagen
        self.menu_vaults.addSeparator()

        # Opción final: Administrar bóvedas / Añadir carpetas
        manage_action = QAction("📁  Administrar bóvedas...", self)
        manage_action.triggered.connect(self.open_manager)
        self.menu_vaults.addAction(manage_action)

    def select_vault(self, folder_path):
        """Cambia la carpeta seleccionada y emite la señal."""
        self.current_folder = folder_path
        self.rebuild_menu()
        self.vault_changed.emit(self.current_folder)

    def open_manager(self):
        """Abre el diálogo para administrar o añadir más carpetas."""
        dialog = VaultManagerDialog(self.folders, parent=self)
        if dialog.exec_():
            self.folders = dialog.folders
            self.save_folders()
            # Si no había ninguna seleccionada, selecciona la primera
            if self.folders and self.current_folder not in self.folders:
                self.current_folder = self.folders[0]
            self.rebuild_menu()