STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    color: #cdd6f4;
    font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
    font-size: 13px;
}

#sidebarContainer {
    background-color: #181825;
    border-right: 1px solid #313244;
}

#sidebarTitle {
    color: #a6adc8;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 6px 4px 2px 4px;
}

/* Lista de notas */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    background-color: transparent;
    color: #bac2de;
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 2px;
}

QListWidget::item:hover {
    background-color: #313244;
    color: #cdd6f4;
}

QListWidget::item:selected {
    background-color: #45475a;
    color: #cba6f7;
    font-weight: 500;
}

/* Botón de nueva nota */
QPushButton#btnNuevaNota {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px;
}

QPushButton#btnNuevaNota:hover {
    background-color: #313244;
}

QPushButton#btnNuevaNota:pressed {
    background-color: #45475a;
}

QTabWidget::pane {
    border: none;
    background-color: #1e1e2e;
}

QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    border: 1px solid transparent;
}

QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #cba6f7;
    font-weight: 600;
    border-bottom: 2px solid #cba6f7;
}

QTabBar::tab:hover:!selected {
    background-color: #313244;
    color: #cdd6f4;
}

QTabBar::close-button {
    image: none;
    subcontrol-position: right;
}

QSplitter::handle {
    background-color: #313244;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QTextEdit {
    background-color: #1e1e2e;
    color: #cdd6f4;
    selection-background-color: #585b70;
    selection-color: #f5e0dc;
    border: none;
    padding: 12px;
    font-family: 'Consolas', 'Fira Code', monospace;
    font-size: 14px;
}

/* Barra de desplazamiento (Scrollbar) */
QScrollBar:vertical {
    border: none;
    background: #1e1e2e;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #45475a;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #585b70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def apply_styles(app):
    app.setStyleSheet(STYLESHEET)