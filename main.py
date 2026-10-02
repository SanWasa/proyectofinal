import sys
import os
import base64
from email.mime.text import MIMEText

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QSplitter, QDialog, QLabel,
    QDateTimeEdit, QLineEdit, QDialogButtonBox, QListWidget, QTextEdit
)
from PyQt5.QtCore import Qt, QDateTime, QThread, pyqtSignal, QTimer

# Importaciones de módulos locales
from modules.folder_selector import VaultSelectorButton
from modules.pestanas import ContenedorPestanas

# Módulo de Markdown integrado en tiempo real (md_2.py)
try:
    from modules.md import ObsidianMarkdownEditor
    MD_EDITOR_DISPONIBLE = True
except ImportError:
    MD_EDITOR_DISPONIBLE = False

# Librería para notificaciones
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

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.send'
]


def apply_style(app, nombre_css="style.css"):
    """Carga y aplica el archivo CSS utilizando la ruta absoluta del archivo."""
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_css = os.path.join(directorio_actual, nombre_css)

    if os.path.exists(ruta_css):
        try:
            with open(ruta_css, "r", encoding="utf-8") as archivo_estilos:
                app.setStyleSheet(archivo_estilos.read())
                print(f"Estilos cargados correctamente desde: {ruta_css}")
        except Exception as e:
            print(f"Error al leer el archivo CSS ({ruta_css}): {e}")
    else:
        print(f"Advertencia: No se encontró el archivo de estilos '{nombre_css}'.")


class HiloLoginGoogle(QThread):
    resultado_signal = pyqtSignal(bool, str, str)

    def run(self):
        if not GOOGLE_DISPONIBLE:
            self.resultado_signal.emit(False, "Faltan librerías de Google o Plyer.", "")
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
                        self.resultado_signal.emit(False, "No se encontró 'credentials.json'.", "")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    credenciales = flow.run_local_server(port=0)

                with open('token.json', 'w') as token_file:
                    token_file.write(credenciales.to_json())

            servicio_oauth = build('oauth2', 'v2', credentials=credenciales)
            info_usuario = servicio_oauth.userinfo().get().execute()
            correo_usuario = info_usuario.get('email', '')

            self.resultado_signal.emit(True, f"Sesión iniciada como {correo_usuario}.", correo_usuario)
        except Exception as e:
            self.resultado_signal.emit(False, str(e), "")


class GestorGmail:
    def __init__(self):
        self.credenciales = None
        self.correo_usuario_actual = ""

    def obtener_credenciales(self):
        if os.path.exists('token.json'):
            self.credenciales = Credentials.from_authorized_user_file('token.json', SCOPES)
        return self.credenciales

    def obtener_correo_sesion(self):
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
        servicio_gmail.users().messages().send(userId='me', body={'raw': raw_message}).execute()

        if PLYER_DISPONIBLE:
            notification.notify(
                title="Correo Notificación Enviado",
                message=f"Se envió el recordatorio de '{titulo_nota}' a {correo_destino}.",
                timeout=5
            )


class DialogoAgendarNota(QDialog):
    def __init__(self, parent=None, nombre_archivo="", correo_por_defecto=""):
        super().__init__(parent)
        self.setWindowTitle("Programar Recordatorio por Correo")
        self.resize(360, 220)

        layout_dialogo = QVBoxLayout()
        layout_dialogo.addWidget(QLabel(f"Configura el envío del correo para '{nombre_archivo}':"))

        layout_dialogo.addWidget(QLabel("Enviar correo a:"))
        self.campo_correo = QLineEdit(correo_por_defecto)
        self.campo_correo.setPlaceholderText("ejemplo@correo.com")
        layout_dialogo.addWidget(self.campo_correo)

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
            QMessageBox.warning(self, "Correo Inválido", "Ingresa un correo válido.")
            return
        
        if self.campo_fecha_hora.dateTime() <= QDateTime.currentDateTime():
            QMessageBox.warning(self, "Fecha Inválida", "La fecha y hora deben ser futuras.")
            return

        self.accept()

    def obtener_datos(self):
        return self.campo_correo.text().strip(), self.campo_fecha_hora.dateTime()


class EditorNotaWidget(QWidget):
    def __init__(self, al_cambiar_callback=None, parent=None):
        super().__init__(parent)
        self.ruta_archivo = None
        self.al_cambiar_callback = al_cambiar_callback

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.campo_titulo = QLineEdit()
        self.campo_titulo.setObjectName("campoTituloNota")
        self.campo_titulo.setPlaceholderText("Título de la nota...")

        if self.al_cambiar_callback:
            self.campo_titulo.textChanged.connect(self.al_cambiar_callback)

        # Usar editor PlanifyMarkdownEditor
        if MD_EDITOR_DISPONIBLE:
            self.editor_texto = ObsidianMarkdownEditor(self)
        else:
            self.editor_texto = QTextEdit()
            print("1")

        self.editor_texto.setObjectName("editorTextoNota")
        self.editor_texto.setPlaceholderText("Escribe tu nota aquí en formato Markdown...")

        if self.al_cambiar_callback:
            self.editor_texto.textChanged.connect(self.al_cambiar_callback)

        layout.addWidget(self.campo_titulo)
        layout.addWidget(self.editor_texto)
        self.setLayout(layout)


class PanelNotasBoveda(QWidget):
    """Panel individual que agrupa un Selector de Bóvedas propio y su contenedor de pestañas."""
    def __init__(self, contador_documentos, config_vaults="vaults.json", parent=None):
        super().__init__(parent)
        self.contador_documentos = contador_documentos

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Barra superior con selector independiente de carpeta
        barra_boveda = QHBoxLayout()
        self.vault_selector = VaultSelectorButton(config_file=config_vaults, parent=self)
        barra_boveda.addWidget(QLabel("Bóveda del Panel:"))
        barra_boveda.addWidget(self.vault_selector)
        barra_boveda.addStretch()

        self.contenedor_pestanas = ContenedorPestanas(self.contador_documentos)

        layout.addLayout(barra_boveda)
        layout.addWidget(self.contenedor_pestanas)
        self.setLayout(layout)


class VentanaPrincipalProyecto(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Planify")
        self.resize(1100, 650)

        self.contador_documentos = {'total': 1}
        self.gestor_gmail = GestorGmail()
        self.temporizadores_correo = []

        # Temporizador para auto-guardado en tiempo real
        self.timer_autoguardado = QTimer(self)
        self.timer_autoguardado.setSingleShot(True)
        self.timer_autoguardado.setInterval(500)
        self.timer_autoguardado.timeout.connect(self.ejecutar_guardado_automatico)

        self.inicializar_interfaz_usuario()

    def inicializar_interfaz_usuario(self):
        # --- PANEL IZQUIERDO (Sidebar principal) ---
        self.lista_notas = QListWidget()
        self.lista_notas.itemClicked.connect(self.cargar_nota_seleccionada)

        self.vault_selector_principal = VaultSelectorButton(config_file="vaults.json", parent=self)
        self.vault_selector_principal.vault_changed.connect(self.on_vault_changed)

        btn_nueva_nota = QPushButton("+ Nueva Nota")
        btn_nueva_nota.clicked.connect(lambda: self.crear_nueva_nota_pestana())

        layout_izquierdo = QVBoxLayout()
        layout_izquierdo.addWidget(QLabel("Notas de la Bóveda"))
        layout_izquierdo.addWidget(btn_nueva_nota)
        layout_izquierdo.addWidget(self.lista_notas)

        footer_izquierdo = QHBoxLayout()
        footer_izquierdo.addWidget(self.vault_selector_principal)
        footer_izquierdo.addStretch()
        layout_izquierdo.addLayout(footer_izquierdo)

        widget_izquierdo = QWidget()
        widget_izquierdo.setObjectName("sidebarContainer")
        widget_izquierdo.setLayout(layout_izquierdo)
        widget_izquierdo.setFixedWidth(250)

        # --- PANEL DERECHO (Barra Superior + Splitter con Paneles Independientes) ---
        layout_controles = QHBoxLayout()
        self.boton_login_google = QPushButton("Iniciar Sesión Google")
        self.boton_logout_google = QPushButton("Cerrar Sesión")
        self.boton_guardar = QPushButton("Guardar Nota")
        self.boton_agendar = QPushButton("Agendar Recordatorio")
        self.boton_borrar = QPushButton("Borrar Nota")
        self.boton_dividir = QPushButton("Vista Dividida")

        self.boton_login_google.clicked.connect(self.iniciar_flujo_login)
        self.boton_logout_google.clicked.connect(self.cerrar_sesion_google)
        self.boton_guardar.clicked.connect(self.guardar_archivo)
        self.boton_agendar.clicked.connect(self.agendar_recordatorio_correo)
        self.boton_borrar.clicked.connect(self.borrar_archivo)
        self.boton_dividir.clicked.connect(self.alternar_vista_dividida)

        layout_controles.addWidget(self.boton_login_google)
        layout_controles.addWidget(self.boton_logout_google)
        layout_controles.addWidget(self.boton_agendar)
        layout_controles.addWidget(self.boton_guardar)
        layout_controles.addWidget(self.boton_borrar)
        layout_controles.addWidget(self.boton_dividir)
        layout_controles.addStretch()

        self.panel_divisor = QSplitter(Qt.Horizontal)

        # Panel Lado Izquierdo/Principal
        self.panel_principal = PanelNotasBoveda(self.contador_documentos)
        self.panel_principal.vault_selector.vault_changed.connect(self.on_vault_changed)
        self.panel_divisor.addWidget(self.panel_principal)

        # Panel Lado Derecho (Vista dividida con selector de bóvedas propio)
        self.panel_secundario = PanelNotasBoveda(self.contador_documentos)
        self.panel_secundario.vault_selector.vault_changed.connect(self.on_vault_changed_secundario)
        self.panel_divisor.addWidget(self.panel_secundario)
        self.panel_secundario.hide()

        layout_derecho = QVBoxLayout()
        layout_derecho.addLayout(layout_controles)
        layout_derecho.addWidget(self.panel_divisor)

        widget_derecho = QWidget()
        widget_derecho.setLayout(layout_derecho)

        # --- LAYOUT PRINCIPAL ---
        layout_principal = QHBoxLayout()
        layout_principal.addWidget(widget_izquierdo)
        layout_principal.addWidget(widget_derecho)

        widget_central = QWidget()
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)

        # Crear primera pestaña al iniciar y cargar lista de la bóveda
        self.crear_nueva_nota_pestana()
        self.actualizar_lista_notas()

    def obtener_panel_activo(self) -> PanelNotasBoveda:
        """Retorna el PanelNotasBoveda que tiene el foco actual."""
        if self.panel_secundario.isVisible() and self.panel_secundario.hasFocus():
            return self.panel_secundario
        return self.panel_principal

    def obtener_contenedor_activo(self):
        """Retorna el contenedor de pestañas activo."""
        return self.obtener_panel_activo().contenedor_pestanas

    def obtener_editor_activo(self) -> EditorNotaWidget:
        """Retorna el widget EditorNotaWidget de la pestaña activa."""
        contenedor = self.obtener_contenedor_activo()
        return contenedor.currentWidget()

    def alternar_vista_dividida(self):
        """Muestra u oculta la vista dividida con selector de carpetas independiente."""
        if self.panel_secundario.isVisible():
            self.panel_secundario.hide()
        else:
            self.panel_secundario.show()
            if self.panel_secundario.contenedor_pestanas.count() == 0:
                self.crear_nueva_nota_pestana(contenedor=self.panel_secundario.contenedor_pestanas)

    def cerrar_sesion_google(self):
        try:
            self.gestor_gmail.cerrar_sesion()
            QMessageBox.information(self, "Sesión Cerrada", "Has cerrado sesión correctamente.")
        except Exception as error:
            QMessageBox.warning(self, "Error al cerrar sesión", str(error))

    def on_vault_changed(self, new_path):
        """Maneja cambios de carpeta en el panel principal."""
        self.vault_selector_principal.current_folder = new_path
        self.actualizar_lista_notas()

    def on_vault_changed_secundario(self, new_path):
        """Maneja cambios de carpeta en la vista dividida secundaria."""
        print(f"Panel Secundario cambió a la bóveda: {new_path}")

    def actualizar_lista_notas(self):
        """Carga en la lista lateral los archivos .md de la bóveda principal."""
        self.lista_notas.clear()
        carpeta_actual = self.vault_selector_principal.current_folder

        if carpeta_actual and os.path.exists(carpeta_actual):
            archivos = [f for f in os.listdir(carpeta_actual) if f.endswith('.md')]
            for archivo in sorted(archivos):
                self.lista_notas.addItem(archivo)

    def crear_nueva_nota_pestana(self, titulo=None, contenedor=None):
        """Crea una nueva pestaña limpia para redactar Markdown."""
        if contenedor is None:
            contenedor = self.obtener_contenedor_activo()

        if titulo is None:
            num_nota = self.contador_documentos['total']
            self.contador_documentos['total'] += 1
            titulo = f"Nota {num_nota}.md"

        editor_widget = EditorNotaWidget(al_cambiar_callback=self.al_cambiar_texto)
        indice = contenedor.addTab(editor_widget, titulo)
        contenedor.setCurrentIndex(indice)
        
        editor_widget.campo_titulo.setFocus()

    def cargar_nota_seleccionada(self, item):
        """Carga el archivo .md en el panel/pestana activa."""
        carpeta_actual = self.vault_selector_principal.current_folder
        if not carpeta_actual:
            return

        ruta_completa = os.path.join(carpeta_actual, item.text())
        if not os.path.exists(ruta_completa):
            return

        contenedor = self.obtener_contenedor_activo()
        editor_actual = self.obtener_editor_activo()

        if editor_actual and not editor_actual.ruta_archivo and not editor_actual.campo_titulo.text().strip() and not editor_actual.editor_texto.toPlainText().strip():
            target_editor = editor_actual
        else:
            target_editor = EditorNotaWidget(al_cambiar_callback=self.al_cambiar_texto)
            indice = contenedor.addTab(target_editor, item.text())
            contenedor.setCurrentIndex(indice)

        target_editor.ruta_archivo = ruta_completa
        nombre_sin_ext, _ = os.path.splitext(item.text())

        target_editor.campo_titulo.blockSignals(True)
        target_editor.editor_texto.blockSignals(True)

        target_editor.campo_titulo.setText(nombre_sin_ext)
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                target_editor.editor_texto.setText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer la nota: {e}")

        target_editor.campo_titulo.blockSignals(False)
        target_editor.editor_texto.blockSignals(False)

        contenedor.setTabText(contenedor.currentIndex(), item.text())

    def al_cambiar_texto(self):
        """Reinicia el temporizador de autoguardado."""
        self.timer_autoguardado.start()

    def ejecutar_guardado_automatico(self):
        """Guarda automáticamente la nota en la bóveda activa según el panel enfocando."""
        editor_actual = self.obtener_editor_activo()
        if not editor_actual:
            return

        panel_activo = self.obtener_panel_activo()
        carpeta_actual = panel_activo.vault_selector.current_folder or self.vault_selector_principal.current_folder

        if not carpeta_actual or not os.path.exists(carpeta_actual):
            return

        titulo = editor_actual.campo_titulo.text().strip()
        contenido = editor_actual.editor_texto.toPlainText()

        if not titulo and not contenido:
            return

        nombre_base = titulo if titulo else "Sin titulo"
        nombre_valido = "".join(c for c in nombre_base if c.isalnum() or c in (" ", "_", "-")).rstrip()
        nuevo_nombre_archivo = f"{nombre_valido}.md"
        nueva_ruta = os.path.join(carpeta_actual, nuevo_nombre_archivo)

        try:
            if editor_actual.ruta_archivo and editor_actual.ruta_archivo != nueva_ruta:
                if os.path.exists(editor_actual.ruta_archivo):
                    os.remove(editor_actual.ruta_archivo)

            with open(nueva_ruta, "w", encoding="utf-8") as f:
                f.write(contenido)

            editor_actual.ruta_archivo = nueva_ruta

            contenedor = panel_activo.contenedor_pestanas
            contenedor.setTabText(contenedor.currentIndex(), nuevo_nombre_archivo)
            self.actualizar_lista_notas()

        except Exception as e:
            print(f"Error en auto-guardado: {e}")


    def agendar_recordatorio_correo(self):
        """Programa el envío del correo para la nota activa."""
        editor_actual = self.obtener_editor_activo()
        if not editor_actual or not editor_actual.ruta_archivo or not os.path.exists(editor_actual.ruta_archivo):
            QMessageBox.warning(self, "Atención", "Guarda o escribe una nota antes de agendar un recordatorio.")
            return

        nombre_archivo = os.path.basename(editor_actual.ruta_archivo)
        correo_sugerido = self.gestor_gmail.obtener_correo_sesion()
        dialogo_agenda = DialogoAgendarNota(self, nombre_archivo, correo_por_defecto=correo_sugerido)

        if dialogo_agenda.exec_() == QDialog.Accepted:
            correo_destino, qdate_seleccionada = dialogo_agenda.obtener_datos()
            try:
                milisegundos_diferencia = QDateTime.currentDateTime().msecsTo(qdate_seleccionada)
                if milisegundos_diferencia > 0:
                    contenido = editor_actual.editor_texto.toPlainText()
                    timer_envio = QTimer(self)
                    timer_envio.setSingleShot(True)
                    timer_envio.timeout.connect(
                        lambda: self.gestor_gmail.enviar_correo_directo_gmail(
                            correo_destino=correo_destino,
                            titulo_nota=nombre_archivo,
                            contenido_nota=contenido,
                            fecha_qdatetime=qdate_seleccionada
                        )
                    )
                    timer_envio.start(milisegundos_diferencia)
                    self.temporizadores_correo.append(timer_envio)

                fecha_formateada = qdate_seleccionada.toString("dd/MM/yyyy hh:mm AP")
                QMessageBox.information(
                    self, "Envío Programado", 
                    f"¡Éxito! El correo se enviará el {fecha_formateada} a '{correo_destino}'."
                )
            except Exception as error_google:
                QMessageBox.warning(self, "Error de Google", str(error_google))


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
        """Elimina el archivo Markdown activo."""
        editor_actual = self.obtener_editor_activo()
        if not editor_actual or not editor_actual.ruta_archivo or not os.path.exists(editor_actual.ruta_archivo):
            QMessageBox.warning(self, "Advertencia", "No hay ninguna nota activa guardada para borrar.")
            return

        confirmacion = QMessageBox.question(
            self, "Confirmar borrado", "¿Deseas borrar esta nota?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirmacion == QMessageBox.Yes:
            try:
                os.remove(editor_actual.ruta_archivo)
                contenedor = self.obtener_contenedor_activo()
                contenedor.cerrar_pestana(contenedor.currentIndex())
                self.actualizar_lista_notas()
                QMessageBox.information(self, "Borrado", "La nota fue eliminada.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"No se pudo borrar el archivo: {error}")

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


if __name__ == "__main__":
    aplicacion = QApplication(sys.argv)
    apply_style(aplicacion, "style.css")

    ventana_principal = VentanaPrincipalProyecto()
    ventana_principal.show()
    sys.exit(aplicacion.exec_())