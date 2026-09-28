import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget
from modules.folder_selector import VaultSelectorButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mi App de Notas")
        self.resize(700, 500)
        # Selector de bóvedas
        self.vault_selector = VaultSelectorButton(config_file="vaults.json", parent=self)
        self.vault_selector.vault_changed.connect(self.on_vault_changed)

        # Layout Principal
        main_layout = QVBoxLayout()
        main_layout.addStretch()  # Empuja la barra inferior al fondo

        # Barra inferior (Footer)
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.vault_selector) # Botón abajo a la izquierda
        footer_layout.addStretch()  # Empuja cualquier otro elemento a la derecha

        main_layout.addLayout(footer_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def on_vault_changed(self, new_path):
        """Aquí puedes cargar las notas o archivos de la carpeta seleccionada."""
        print(f"Bóveda activa cambiada a: {new_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())