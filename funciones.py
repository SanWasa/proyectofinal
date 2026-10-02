from PyQt5.QtWidgets import QMessageBox, QFileDialog
import os

def abrir_archivo(self):
        """Abre y permite revisar archivos en formato .md"""
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, 
            "Abrir archivo Markdown", 
            "", 
            "Archivos Markdown (*.md);;Todos los archivos (*)"
        )
        if ruta_archivo:
            try:
                with open(ruta_archivo, "r", encoding="utf-8") as archivo_lectura:
                    self.editor_texto.setText(archivo_lectura.read())
                self.archivo_actual = ruta_archivo
            except Exception as error_detallado:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo: {error_detallado}")

def guardar_archivo(self):
    """Guarda el contenido en formato .md"""
    if not self.archivo_actual:
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar archivo Markdown", 
            "", 
            "Archivos Markdown (*.md);;Todos los archivos (*)"
        )
        if not ruta_archivo:
            return
        
        if not ruta_archivo.endswith(".md"):
            ruta_archivo += ".md"
        self.archivo_actual = ruta_archivo

    try:
        with open(self.archivo_actual, "w", encoding="utf-8") as archivo_escritura:
            archivo_escritura.write(self.editor_texto.toPlainText())
        QMessageBox.information(self, "Guardado", "Archivo guardado exitosamente.")
    except Exception as error_detallado:
        QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {error_detallado}")

def borrar_archivo(self):
    """Elimina el archivo .md del sistema"""
    if not self.archivo_actual or not os.path.exists(self.archivo_actual):
        QMessageBox.warning(self, "Advertencia", "No hay ningún archivo abierto para borrar.")
        return

    confirmacion_usuario = QMessageBox.question(
        self,
        "Confirmar borrado",
        "¿Deseas borrar este archivo .md?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if confirmacion_usuario == QMessageBox.Yes:
        try:
            os.remove(self.archivo_actual)
            self.editor_texto.clear()
            self.archivo_actual = None
            QMessageBox.information(self, "Borrado", "El archivo fue eliminado.")
        except Exception as error_detallado:
            QMessageBox.critical(self, "Error", f"No se pudo borrar el archivo: {error_detallado}")