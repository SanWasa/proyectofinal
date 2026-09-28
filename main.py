import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, 
    QVBoxLayout, QWidget, QLabel, QAction
)
from folder_selector import FolderManager
from folder_selector import FolderSelectorDialog

class MainWindow(QMainWindow):
    def __init__(self, vault_manager: VaultManager):
        super().__init__()
        self.vault_mgr = vault_manager
        self.resize(800, 600)
        
        self.init_ui()
        self.update_title()

    def init_ui(self):
        # Barra de menú superior (Menu > Cambiar Bóveda)
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Archivo")
        
        change_vault_action = QAction("Cambiar Bóveda...", self)
        change_vault_action.triggered.connect(self.open_vault_selector)
        file_menu.addAction(change_vault_action)

        # Contenido principal
        container = QWidget()
        layout = QVBoxLayout()

        self.lbl_info = QLabel()
        layout.addWidget(self.lbl_info)

        btn_change = QPushButton("Abrir otra bóveda")
        btn_change.clicked.connect(self.open_vault_selector)
        layout.addWidget(btn_change)

        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_title(self):
        current_vault = self.vault_mgr.get_current_vault()
        self.setWindowTitle(f"Mis Notas - Bóveda: {current_vault}")
        self.lbl_info.setText(f"Cargando notas desde: {current_vault}")

    def open_vault_selector(self):
        # Abrir el módulo de diálogo
        dialog = VaultSelectorDialog(self, self.vault_mgr.get_current_vault())
        if dialog.exec_():
            nueva_boveda = dialog.selected_vault
            self.vault_mgr.set_vault(nueva_boveda)
            self.update_title()

def main():
    app = QApplication(sys.argv)
    vault_mgr = FolderManager()

    # Si no hay bóveda guardada previo al inicio, forzar la selección estilo Obsidian
    if not vault_mgr.get_current_vault():
        dialog = FolderSelectorDialog()
        if not dialog.exec_():
            # Si el usuario cierra el diálogo sin elegir nada, salir de la app
            sys.exit(0)
        vault_mgr.set_vault(dialog.selected_vault)

    window = MainWindow(vault_mgr)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()