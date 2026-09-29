import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, 
    QWidget, QTextEdit, QListWidget, QLabel
)
from modules.folder_selector import VaultSelectorButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mi App de Notas")
        self.resize(900, 600)

        # --- COMPONENTES ---
        # 1. Editor de texto (Derecha)
        self.texto = QTextEdit()
        self.texto.setPlaceholderText("Escribe tu nota aquí...")

        # 2. Lista para ver las notas (Izquierda)
        self.lista_notas = QListWidget()
        
        # 3. Selector de bóvedas (Abajo a la izquierda)
        self.vault_selector = VaultSelectorButton(config_file="vaults.json", parent=self)
        self.vault_selector.vault_changed.connect(self.on_vault_changed)

        # --- LAYOUTS ---
        
        # Panel Izquierdo (Sidebar): Lista de notas + Botón de bóveda abajo
        layout_izquierdo = QVBoxLayout()
        
        etiqueta_notas = QLabel("Notas")
        layout_izquierdo.addWidget(etiqueta_notas)
        layout_izquierdo.addWidget(self.lista_notas)
        
        # Footer del panel izquierdo para situar la bóveda al fondo
        footer_izquierdo = QHBoxLayout()
        footer_izquierdo.addWidget(self.vault_selector)
        footer_izquierdo.addStretch()  # Empuja el selector a la izquierda
        
        layout_izquierdo.addLayout(footer_izquierdo)

        # Contenedor del panel izquierdo
        widget_izquierdo = QWidget()
        widget_izquierdo.setLayout(layout_izquierdo)
        widget_izquierdo.setFixedWidth(250)  # Ancho fijo para el panel lateral

        # Layout Principal (Horizontal): Panel Izquierdo | Editor de Texto
        layout_principal = QHBoxLayout()
        layout_principal.addWidget(widget_izquierdo)
        layout_principal.addWidget(self.texto)

        # Configurar widget central
        container = QWidget()
        container.setLayout(layout_principal)
        self.setCentralWidget(container)

    def on_vault_changed(self, new_path):
        """Aquí puedes cargar las notas o archivos de la carpeta seleccionada."""
        print(f"Bóveda activa cambiada a: {new_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())