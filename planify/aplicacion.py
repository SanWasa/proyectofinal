import sys
import os
import datetime
import base64
from email.mime.text import MIMEText

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QTabWidget,
    QToolButton, QSplitter, QDialog, QLabel, QDateTimeEdit, QLineEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QDateTime, QThread, pyqtSignal, QTimer

# Librería para notificaciones de escritorio
try:
    from plyer import notification
    PLYER_DISPONIBLE = True
except ImportError:
    PLYER_DISPONIBLE = False

# Librerías de Google
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_DISPONIBLE = True
except ImportError:
    GOOGLE_DISPONIBLE = False

# Permisos para Gmail, Perfil de Usuario y OpenID
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.send'
]


class HiloLoginGoogle(QThread):
    """Ejecuta la autenticación de Google en segundo plano."""
    resultado_signal = pyqtSignal(bool, str, str)

    def run(self):
        if not GOOGLE_DISPONIBLE:
            self.resultado_signal.emit(False, "Faltan librerías. Instala: pip install google-auth-oauthlib google-api-python-client plyer", "")
            return

        try:
            credenciales = None
            if os.path.exists('token.json'):
                credenciales = Credentials.from_authorized_user_file('token.json', SCOPES)

            if not credenciales or not credenciales.valid:
                if credenciales and credenciales.expired and credenciales.refresh_token:
                    credenciales.refresh(Request())
                else:
                    if not os.path.exists('credentials.json'):
                        self.resultado_signal.emit(False, "No se encontró el archivo 'credentials.json' de Google Cloud.", "")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    credenciales = flow.run_local_server(port=0)

                with open('token.json', 'w') as token_file:
                    token_file.write(credenciales.to_json())

            # Obtener el correo del usuario
            servicio_oauth = build('oauth2', 'v2', credentials=credenciales)
            info_usuario = servicio_oauth.userinfo().get().execute()
            correo_usuario = info_usuario.get('email', '')

            self.resultado_signal.emit(True, f"Sesión iniciada con éxito para {correo_usuario}.", correo_usuario)
        except Exception as e:
            self.resultado_signal.emit(False, str(e), "")


class GestorGmail:
    """Maneja la autenticación y el envío de correos por Gmail."""
    def __init__(self):
        self.credenciales = None
        self.correo_usuario_actual = ""

    def obtener_credenciales(self):
        if os.path.exists('token.json'):
            self.credenciales = Credentials.from_authorized_user_file('token.json', SCOPES)
        return self.credenciales

    def obtener_correo_sesion(self):
        """Consulta la dirección de correo de la cuenta conectada."""
        if self.correo_usuario_actual:
            return self.correo_usuario_actual
        
        credenciales = self.obtener_credenciales()
        if credenciales:
            try:
                servicio_oauth = build('oauth2', 'v2', credentials=credenciales)
                info_usuario = servicio_oauth.userinfo().get().execute()
                self.correo_usuario_actual = info_usuario.get('email', '')
            except Exception:
                pass
        return self.correo_usuario_actual

    def cerrar_sesion(self):
        """Elimina el archivo token.json para cerrar la sesión activa."""
        self.credenciales = None
        self.correo_usuario_actual = ""
        if os.path.exists('token.json'):
            try:
                os.remove('token.json')
                return True
            except Exception as e:
                raise Exception(f"No se pudo eliminar el token de sesión: {e}")
        return True

    def enviar_correo_directo_gmail(self, correo_destino, titulo_nota, contenido_nota, fecha_qdatetime):
        """Envía el correo directamente mediante la API de Gmail."""
        credenciales = self.obtener_credenciales()
        if not credenciales:
            raise Exception("No has iniciado sesión con tu cuenta de Google.")

        servicio_gmail = build('gmail', 'v1', credentials=credenciales)
        fecha_texto = fecha_qdatetime.toString("dd/MM/yyyy hh:mm AP")

        cuerpo_mensaje = f"""Hola,

Este es el recordatorio automático de tu nota agendada en planify.

Detalles de la nota:
--------------------------------------------------
Título: {titulo_nota}
Fecha/Hora Programada: {fecha_texto}

Contenido:
{contenido_nota}
--------------------------------------------------
"""

        mensaje = MIMEText(cuerpo_mensaje, 'plain', 'utf-8')
        mensaje['To'] = correo_destino
        mensaje['Subject'] = f"Recordatorio de Nota: {titulo_nota}"

        raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode('utf-8')
        cuerpo_envio = {'raw': raw_message}

        servicio_gmail.users().messages().send(userId='me', body=cuerpo_envio).execute()

        if PLYER_DISPONIBLE:
            notification.notify(
                title="Correo Notificación Enviado",
                message=f"Se envió el recordatorio de '{titulo_nota}' a {correo_destino}.",
                timeout=5
            )


class DialogoAgendarNota(QDialog):
    """Diálogo para seleccionar fecha/hora e ingresar el correo de destino."""
    def __init__(self, parent=None, nombre_archivo="", correo_por_defecto=""):
        super().__init__(parent)
        self.setWindowTitle("Programar Recordatorio por Correo")
        self.resize(360, 220)

        layout_dialogo = QVBoxLayout()

        etiqueta_info = QLabel(f"Configura el envío del correo para '{nombre_archivo}':")
        etiqueta_info.setWordWrap(True)
        layout_dialogo.addWidget(etiqueta_info)

        # Campo para que la persona coloque al correo que lo quiera enviar
        layout_dialogo.addWidget(QLabel("Enviar correo a:"))
        self.campo_correo = QLineEdit(correo_por_defecto)
        self.campo_correo.setPlaceholderText("ejemplo@correo.com")
        layout_dialogo.addWidget(self.campo_correo)

        # Campo para que la persona coloque fecha y hora para recibirlo
        layout_dialogo.addWidget(QLabel("Fecha y hora de envío:"))
        self.campo_fecha_hora = QDateTimeEdit(QDateTime.currentDateTime().addSecs(300))
        self.campo_fecha_hora.setCalendarPopup(True)
        self.campo_fecha_hora.setDisplayFormat("dd/MM/yyyy hh:mm AP")
        layout_dialogo.addWidget(self.campo_fecha_hora)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.validar_y_aceptar)
        botones.rejected.connect(self.reject)
        layout_dialogo.addWidget(botones)

        self.setLayout(layout_dialogo)

    def validar_y_aceptar(self):
        correo = self.campo_correo.text().strip()
        if not correo or "@" not in correo or "." not in correo:
            QMessageBox.warning(self, "Correo Inválido", "Por favor ingresa una dirección de correo válida.")
            return
        
        if self.campo_fecha_hora.dateTime() <= QDateTime.currentDateTime():
            QMessageBox.warning(self, "Fecha Inválida", "La fecha y hora deben ser futuras.")
            return

        self.accept()

    def obtener_datos(self):
        return self.campo_correo.text().strip(), self.campo_fecha_hora.dateTime()


class PestanaEditor(QWidget):
    def __init__(self, ruta_archivo=None):
        super().__init__()
        self.ruta_archivo = ruta_archivo
        
        layout_pestana = QVBoxLayout()
        layout_pestana.setContentsMargins(0, 0, 0, 0)
        
        self.editor_texto = QTextEdit()
        layout_pestana.addWidget(self.editor_texto)
        self.setLayout(layout_pestana)


class ContenedorPestanas(QTabWidget):
    def __init__(self, contador_global_referencia):
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.cerrar_pestana)
        self.contador_global = contador_global_referencia

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


class VentanaPrincipalProyecto(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("planify")
        self.setGeometry(100, 100, 1000, 600)

        self.contador_documentos = {'total': 1}
        self.gestor_gmail = GestorGmail()
        self.temporizadores_correo = []  # Mantiene los QTimer activos

        self.inicializar_interfaz_usuario()

    def inicializar_interfaz_usuario(self):
        widget_central = QWidget()
        layout_principal = QVBoxLayout()

        layout_controles = QHBoxLayout()

        self.boton_login_google = QPushButton("Iniciar Sesión Google")
        self.boton_logout_google = QPushButton("Cerrar Sesión")
        self.boton_abrir = QPushButton("Abrir")
        self.boton_guardar = QPushButton("Guardar y Agendar")
        self.boton_borrar = QPushButton("Borrar Archivo")
        self.boton_dividir = QPushButton("Vista Dividida")

        self.boton_login_google.clicked.connect(self.iniciar_flujo_login)
        self.boton_logout_google.clicked.connect(self.cerrar_sesion_google)
        self.boton_abrir.clicked.connect(self.abrir_archivo)
        self.boton_guardar.clicked.connect(self.guardar_archivo)
        self.boton_borrar.clicked.connect(self.borrar_archivo)
        self.boton_dividir.clicked.connect(self.alternar_vista_dividida)

        layout_controles.addWidget(self.boton_login_google)
        layout_controles.addWidget(self.boton_logout_google)
        layout_controles.addWidget(self.boton_abrir)
        layout_controles.addWidget(self.boton_guardar)
        layout_controles.addWidget(self.boton_borrar)
        layout_controles.addWidget(self.boton_dividir)
        layout_controles.addStretch()

        layout_principal.addLayout(layout_controles)

        self.panel_divisor = QSplitter(Qt.Horizontal)

        self.contenedor_principal = ContenedorPestanas(self.contador_documentos)
        self.contenedor_principal.agregar_nueva_pestana()
        self.panel_divisor.addWidget(self.contenedor_principal)

        self.contenedor_secundario = ContenedorPestanas(self.contador_documentos)
        self.panel_divisor.addWidget(self.contenedor_secundario)
        self.contenedor_secundario.hide()

        layout_principal.addWidget(self.panel_divisor)
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)

    def iniciar_flujo_login(self):
        self.hilo_login = HiloLoginGoogle()
        self.hilo_login.resultado_signal.connect(self.resultado_login)
        self.hilo_login.start()

    def resultado_login(self, exito, mensaje, correo):
        if exito:
            self.gestor_gmail.correo_usuario_actual = correo
            QMessageBox.information(self, "Google", mensaje)
        else:
            QMessageBox.critical(self, "Error de Sesión", mensaje)

    def cerrar_sesion_google(self):
        try:
            self.gestor_gmail.cerrar_sesion()
            QMessageBox.information(self, "Sesión Cerrada", "Has cerrado sesión correctamente.")
        except Exception as error:
            QMessageBox.warning(self, "Error al cerrar sesión", str(error))

    def obtener_contenedor_activo(self):
        if self.contenedor_secundario.isVisible() and self.contenedor_secundario.hasFocus():
            return self.contenedor_secundario
        return self.contenedor_principal

    def obtener_editor_activo(self):
        return self.obtener_contenedor_activo().currentWidget()

    def alternar_vista_dividida(self):
        if self.contenedor_secundario.isVisible():
            self.contenedor_secundario.hide()
        else:
            self.contenedor_secundario.show()
            if self.contenedor_secundario.count() == 0:
                self.contenedor_secundario.agregar_nueva_pestana()

    def abrir_archivo(self):
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo Markdown", "", "Archivos Markdown (*.md);;Todos los archivos (*)"
        )
        if ruta_archivo:
            try:
                with open(ruta_archivo, "r", encoding="utf-8") as archivo_lectura:
                    contenido = archivo_lectura.read()
                
                contenedor_activo = self.obtener_contenedor_activo()
                pestana_actual = contenedor_activo.currentWidget()

                if pestana_actual and (pestana_actual.ruta_archivo or pestana_actual.editor_texto.toPlainText().strip()):
                    nombre_archivo = os.path.basename(ruta_archivo)
                    nueva_pestana = contenedor_activo.agregar_nueva_pestana(nombre_archivo, contenido)
                    nueva_pestana.ruta_archivo = ruta_archivo
                else:
                    pestana_actual.editor_texto.setText(contenido)
                    pestana_actual.ruta_archivo = ruta_archivo
                    nombre_archivo = os.path.basename(ruta_archivo)
                    contenedor_activo.setTabText(contenedor_activo.currentIndex(), nombre_archivo)

            except Exception as error:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo: {error}")

    def guardar_archivo(self):
        pestana_actual = self.obtener_editor_activo()
        if not pestana_actual:
            return

        if not pestana_actual.ruta_archivo:
            ruta_archivo, _ = QFileDialog.getSaveFileName(
                self, "Guardar archivo Markdown", "", "Archivos Markdown (*.md);;Todos los archivos (*)"
            )
            if not ruta_archivo:
                return
            
            if not ruta_archivo.endswith(".md"):
                ruta_archivo += ".md"
            pestana_actual.ruta_archivo = ruta_archivo

        try:
            contenido = pestana_actual.editor_texto.toPlainText()
            with open(pestana_actual.ruta_archivo, "w", encoding="utf-8") as archivo_escritura:
                archivo_escritura.write(contenido)

            nombre_solo = os.path.basename(pestana_actual.ruta_archivo)
            contenedor_activo = self.obtener_contenedor_activo()
            contenedor_activo.setTabText(contenedor_activo.currentIndex(), nombre_solo)

            correo_sugerido = self.gestor_gmail.obtener_correo_sesion()
            dialogo_agenda = DialogoAgendarNota(self, nombre_solo, correo_por_defecto=correo_sugerido)
            
            if dialogo_agenda.exec_() == QDialog.Accepted:
                correo_destino, qdate_seleccionada = dialogo_agenda.obtener_datos()

                try:
                    milisegundos_diferencia = QDateTime.currentDateTime().msecsTo(qdate_seleccionada)

                    if milisegundos_diferencia > 0:
                        timer_envio = QTimer(self)
                        timer_envio.setSingleShot(True)
                        timer_envio.timeout.connect(
                            lambda: self.gestor_gmail.enviar_correo_directo_gmail(
                                correo_destino=correo_destino,
                                titulo_nota=nombre_solo,
                                contenido_nota=contenido,
                                fecha_qdatetime=qdate_seleccionada
                            )
                        )
                        timer_envio.start(milisegundos_diferencia)
                        self.temporizadores_correo.append(timer_envio)

                    fecha_formateada = qdate_seleccionada.toString("dd/MM/yyyy hh:mm AP")
                    QMessageBox.information(
                        self, 
                        "Envío Programado", 
                        f"¡Éxito! El correo se enviará automáticamente el {fecha_formateada} a '{correo_destino}'."
                    )
                except Exception as error_google:
                    QMessageBox.warning(
                        self, 
                        "Guardado con Advertencia", 
                        f"El archivo se guardó localmente, pero ocurrió un error con la cuenta de Google:\n{error_google}"
                    )
            else:
                QMessageBox.information(self, "Guardado", "El archivo .md se guardó sin agendar fecha.")

        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {error}")

    def borrar_archivo(self):
        pestana_actual = self.obtener_editor_activo()
        if not pestana_actual or not pestana_actual.ruta_archivo or not os.path.exists(pestana_actual.ruta_archivo):
            QMessageBox.warning(self, "Advertencia", "No hay ningún archivo .md abierto para borrar.")
            return

        confirmacion = QMessageBox.question(
            self, "Confirmar borrado", "¿Deseas borrar este archivo .md?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirmacion == QMessageBox.Yes:
            try:
                os.remove(pestana_actual.ruta_archivo)
                contenedor_activo = self.obtener_contenedor_activo()
                contenedor_activo.cerrar_pestana(contenedor_activo.currentIndex())
                QMessageBox.information(self, "Borrado", "El archivo fue eliminado.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"No se pudo borrar el archivo: {error}")


if __name__ == "__main__":
    aplicacion = QApplication(sys.argv)
    ventana_principal = VentanaPrincipalProyecto()
    ventana_principal.show()
    sys.exit(aplicacion.exec_())