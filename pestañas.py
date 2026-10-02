from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QTabWidget, QToolButton, QSplitter
from PyQt5.QtCore import Qt


class PestanaEditor(QWidget):
    """Representa cada documento individual dentro de las pestañas."""
    def __init__(self, ruta_archivo=None):
        super().__init__()
        self.ruta_archivo = ruta_archivo
        
        layout_pestana = QVBoxLayout()
        layout_pestana.setContentsMargins(0, 0, 0, 0)
        
        self.editor_texto = QTextEdit()
        layout_pestana.addWidget(self.editor_texto)
        self.setLayout(layout_pestana)


class ContenedorPestanas(QTabWidget):
    """Gestor de pestañas individual con botón '+' en la esquina."""
    def __init__(self, contador_global_referencia):
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.cerrar_pestana)
        self.contador_global = contador_global_referencia

        # este es el botón + ppara agregar pas pestañas
        self.boton_agregar_pestana = QToolButton(self)
        self.boton_agregar_pestana.setText("+")
        self.boton_agregar_pestana.setToolTip("Nueva Pestaña")
        self.boton_agregar_pestana.setStyleSheet(
            "QToolButton { font-weight: bold; font-size: 14px; padding: 2px 8px; }"
        )
        self.boton_agregar_pestana.clicked.connect(lambda: self.agregar_nueva_pestana())

        self.setCornerWidget(self.boton_agregar_pestana, Qt.TopRightCorner)

    def agregar_nueva_pestana(self, titulo=None, contenido=""):
        if not titulo:
            numero_documento = self.contador_global['total']
            titulo = f"Sin título {numero_documento}" if numero_documento > 1 else "Sin título"
            self.contador_global['total'] += 1

        pestana_nueva = PestanaEditor()
        pestana_nueva.editor_texto.setText(contenido)
        indice = self.addTab(pestana_nueva, titulo)
        self.setCurrentIndex(indice)
        return pestana_nueva

    def cerrar_pestana(self, indice):
        if self.count() > 1:
            self.removeTab(indice)
        else:
            pestana_actual = self.widget(indice)
            pestana_actual.editor_texto.clear()
            pestana_actual.ruta_archivo = None
            self.setTabText(indice, "Sin título")


class GestorVistaDividida:
    """Clase auxiliar para manejar los dos paneles del QSplitter."""
    def __init__(self, contador_global):
        self.contador = contador_global
        self.panel_divisor = QSplitter(Qt.Horizontal)

        # pantalla dividada en la izquierda principal
        self.panel_izquierdo = ContenedorPestanas(self.contador)
        self.panel_izquierdo.agregar_nueva_pestana()
        self.panel_divisor.addWidget(self.panel_izquierdo)

        # Pantalla dividida en la derecha
        self.panel_derecho = ContenedorPestanas(self.contador)
        self.panel_divisor.addWidget(self.panel_derecho)
        self.panel_derecho.hide()

    def alternar_vista(self):
        """Muestra u oculta el panel derecho."""
        if self.panel_derecho.isVisible():
            self.panel_derecho.hide()
        else:
            self.panel_derecho.show()
            if self.panel_derecho.count() == 0:
                self.panel_derecho.agregar_nueva_pestana()