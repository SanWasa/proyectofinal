import re

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter


class MarkdownLiveHighlighter(QSyntaxHighlighter):
    """Highlighter Markdown con apariencia tipo Obsidian.

    En bloques que no están activos, oculta los marcadores Markdown
    que normalmente no se muestran en modo lectura, pero mantiene
    visibles los números de las listas ordenadas.
    """

    def __init__(self, document):
        super().__init__(document)

        # -1 = ningún bloque activo. Esto permite que al abrir una nota
        # aparezca inicialmente en modo "renderizado".
        self.active_block_number = -1

        self.bg_color = QColor("#1e1e2e")
        self.text_color = "#cdd6f4"

        self.rehighlight()

    def set_active_block(self, block_number):
        if self.active_block_number != block_number:
            self.active_block_number = block_number
            self.rehighlight()

    def highlightBlock(self, text):
        current_block = self.currentBlock().blockNumber()
        is_active = current_block == self.active_block_number

        # ---------------------------------------------------------
        # ENCABEZADOS
        # ---------------------------------------------------------
        header_match = re.match(r"^(#{1,6})(?:\s+)(.*)$", text)
        if header_match:
            hash_len = len(header_match.group(1))
            content_start = header_match.start(2)

            if is_active:
                self._format_visible(0, content_start, "#569cd6", bold=True)
                self._format_text(
                    content_start,
                    len(text) - content_start,
                    "#ffffff",
                    size={1: 22, 2: 18, 3: 16, 4: 15, 5: 14, 6: 13}.get(hash_len, 14),
                    bold=True,
                )
            else:
                self._format_hidden(0, content_start)
                self._format_text(
                    content_start,
                    len(text) - content_start,
                    "#ffffff",
                    size={1: 22, 2: 18, 3: 16, 4: 15, 5: 14, 6: 13}.get(hash_len, 14),
                    bold=True,
                )
            return

        # ---------------------------------------------------------
        # ALERTAS / CALLOUTS
        # Ejemplo: > [!NOTE] texto
        # ---------------------------------------------------------
        alert_match = re.match(
            r"^(\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\])(.*)$",
            text,
            re.IGNORECASE,
        )

        if alert_match:
            mark_len = len(alert_match.group(1))
            alert_type = alert_match.group(2).upper()

            colors = {
                "NOTE": "#0969da",
                "TIP": "#1a7f37",
                "IMPORTANT": "#8250df",
                "WARNING": "#9a6700",
                "CAUTION": "#cf222e",
            }
            color = colors.get(alert_type, "#569cd6")

            if is_active:
                self._format_visible(0, mark_len, color, bold=True)
            else:
                self._format_hidden(0, mark_len)

            self._format_text(
                mark_len,
                len(text) - mark_len,
                color,
                bold=True,
            )
            return

        # ---------------------------------------------------------
        # CITAS
        # ---------------------------------------------------------
        quote_match = re.match(r"^(\s*>+)(.*)$", text)
        if quote_match:
            quote_mark_len = len(quote_match.group(1))

            if is_active:
                self._format_visible(0, quote_mark_len, "#6a9955", bold=True)
            else:
                self._format_hidden(0, quote_mark_len)

            self._format_text(
                quote_mark_len,
                len(text) - quote_mark_len,
                "#6a9955",
                italic=True,
            )
            return

        # ---------------------------------------------------------
        # CHECKLIST
        # Ejemplo: - [ ] tarea / - [x] tarea
        # ---------------------------------------------------------
        task_match = re.match(r"^(\s*[-*+]\s+\[[ xX]\])(\s*)(.*)$", text)
        if task_match:
            prefix_len = len(task_match.group(1)) + len(task_match.group(2))

            if is_active:
                self._format_visible(
                    0,
                    len(task_match.group(1)),
                    "#4ec9b0",
                    bold=True,
                )
            else:
                self._format_hidden(0, len(task_match.group(1)))

            # Mantener el espacio y el texto normales.
            if prefix_len < len(text):
                self._format_text(
                    prefix_len,
                    len(text) - prefix_len,
                    self.text_color,
                )
            return

        # ---------------------------------------------------------
        # LISTA ORDENADA
        # IMPORTANTE: los números NO desaparecen al desactivar
        # la línea.
        #
        # Detecta:
        # 1. elemento
        # 2. elemento
        # 10. elemento
        # ---------------------------------------------------------
        ordered_match = re.match(r"^(\s*\d+\.\s+)(.*)$", text)
        if ordered_match:
            number_len = len(ordered_match.group(1))

            if is_active:
                # Número visible como marcador de edición.
                self._format_visible(
                    0,
                    number_len,
                    "#b5cea8",
                    bold=True,
                )
            else:
                # NO usar _format_hidden aquí.
                # El número debe seguir visible.
                self._format_text(
                    0,
                    number_len,
                    "#b5cea8",
                    bold=True,
                )

            if number_len < len(text):
                self._format_text(
                    number_len,
                    len(text) - number_len,
                    self.text_color,
                )

            return

        # ---------------------------------------------------------
        # LISTA NO ORDENADA
        # ---------------------------------------------------------
        unordered_match = re.match(r"^(\s*[-*+]\s+)(.*)$", text)
        if unordered_match:
            bullet_len = len(unordered_match.group(1))

            if is_active:
                self._format_visible(
                    0,
                    bullet_len,
                    "#ce9178",
                    bold=True,
                )
            else:
                self._format_hidden(0, bullet_len)

            if bullet_len < len(text):
                self._format_text(
                    bullet_len,
                    len(text) - bullet_len,
                    self.text_color,
                )

            return

        # ---------------------------------------------------------
        # TABLAS
        # ---------------------------------------------------------
        if text.strip().startswith("|") and text.strip().endswith("|"):
            for match in re.finditer(r"\|", text):
                if is_active:
                    self._format_visible(
                        match.start(),
                        1,
                        "#569cd6",
                        bold=True,
                    )
                else:
                    self._format_hidden(match.start(), 1)

            return

        # ---------------------------------------------------------
        # BLOQUES DE CÓDIGO
        # ---------------------------------------------------------
        if text.strip().startswith("```"):
            if is_active:
                self._format_visible(
                    0,
                    len(text),
                    "#808080",
                    bold=True,
                )
            else:
                self._format_hidden(0, len(text))
            return

        # ---------------------------------------------------------
        # FORMATO INLINE
        # ---------------------------------------------------------
        self._process_inline_wrapper(
            text,
            r"(\*\*|__)(.+?)\1",
            2,
            is_active,
            bold=True,
        )

        self._process_inline_wrapper(
            text,
            r"(?<!\*)\*([^*\n]+?)\*(?!\*)",
            1,
            is_active,
            italic=True,
        )

        self._process_inline_wrapper(
            text,
            r"(?<!\w)_([^_\n]+?)_(?!\w)",
            1,
            is_active,
            italic=True,
        )

        self._process_inline_wrapper(
            text,
            r"~~(.+?)~~",
            2,
            is_active,
            strike=True,
        )

        self._process_inline_wrapper(
            text,
            r"`([^`\n]+?)`",
            1,
            is_active,
            color="#ce9178",
            bg="#2d2d2d",
        )

        self._process_inline_wrapper(
            text,
            r"\$([^$\n]+?)\$",
            1,
            is_active,
            color="#dcdcaa",
        )

        # ---------------------------------------------------------
        # HTML
        # ---------------------------------------------------------
        for match in re.finditer(r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?>", text):
            start, end = match.span()

            if is_active:
                self._format_visible(start, end - start, "#808080")
            else:
                self._format_hidden(start, end - start)

        # ---------------------------------------------------------
        # ENLACES / IMÁGENES
        # ---------------------------------------------------------
        for match in re.finditer(
            r"(!?\[)([^\]]+)(\]\([^)]+\))",
            text,
        ):
            start, end = match.span()

            open_bracket_len = len(match.group(1))
            content_len = len(match.group(2))
            close_url_len = len(match.group(3))

            if is_active:
                self._format_visible(
                    start,
                    open_bracket_len,
                    "#569cd6",
                )
                self._format_text(
                    start + open_bracket_len,
                    content_len,
                    "#4fc1ff",
                    underline=True,
                )
                self._format_visible(
                    start + open_bracket_len + content_len,
                    close_url_len,
                    "#569cd6",
                )
            else:
                self._format_hidden(
                    start,
                    open_bracket_len,
                )
                self._format_text(
                    start + open_bracket_len,
                    content_len,
                    "#4fc1ff",
                    underline=True,
                )
                self._format_hidden(
                    start + open_bracket_len + content_len,
                    close_url_len,
                )

        # ---------------------------------------------------------
        # MENCIONES
        # ---------------------------------------------------------
        for match in re.finditer(r"(@\w+|#\d+)", text):
            start, end = match.span()

            if is_active:
                self._format_visible(
                    start,
                    end - start,
                    "#4fc1ff",
                    bold=True,
                )
            else:
                self._format_text(
                    start,
                    end - start,
                    "#4fc1ff",
                    bold=True,
                )

        # ---------------------------------------------------------
        # NOTAS AL PIE
        # ---------------------------------------------------------
        for match in re.finditer(r"(\[\^)(\d+)(\])", text):
            start, end = match.span()

            if is_active:
                self._format_visible(
                    start,
                    end - start,
                    "#b5cea8",
                )
            else:
                self._format_hidden(start, 2)
                self._format_text(
                    start + 2,
                    len(match.group(2)),
                    "#b5cea8",
                )
                self._format_hidden(end - 1, 1)

    # =============================================================
    # MÉTODOS AUXILIARES
    # =============================================================

    def _format_visible(self, start, length, color_hex, bold=False):
        if length <= 0:
            return

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))

        if bold:
            fmt.setFontWeight(QFont.Bold)

        self.setFormat(start, length, fmt)

    def _format_hidden(self, start, length):
        if length <= 0:
            return

        fmt = QTextCharFormat()
        fmt.setForeground(self.bg_color)
        fmt.setFontPointSize(1)
        self.setFormat(start, length, fmt)

    def _format_text(
        self,
        start,
        length,
        color_hex,
        size=None,
        bold=False,
        italic=False,
        strike=False,
        underline=False,
        bg=None,
    ):
        if length <= 0:
            return

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))

        if size:
            fmt.setFontPointSize(size)

        if bold:
            fmt.setFontWeight(QFont.Bold)

        if italic:
            fmt.setFontItalic(True)

        if strike:
            fmt.setFontStrikeOut(True)

        if underline:
            fmt.setFontUnderline(True)

        if bg:
            fmt.setBackground(QColor(bg))

        self.setFormat(start, length, fmt)

    def _process_inline_wrapper(
        self,
        text,
        pattern,
        mark_len,
        is_active,
        bold=False,
        italic=False,
        strike=False,
        color="#d4d4d4",
        bg=None,
    ):
        for match in re.finditer(pattern, text):
            start, end = match.span()

            content_len = (end - start) - (2 * mark_len)

            if content_len <= 0:
                continue

            if is_active:
                self._format_visible(
                    start,
                    mark_len,
                    "#569cd6",
                )

                self._format_text(
                    start + mark_len,
                    content_len,
                    color,
                    bold=bold,
                    italic=italic,
                    strike=strike,
                    bg=bg,
                )

                self._format_visible(
                    end - mark_len,
                    mark_len,
                    "#569cd6",
                )
            else:
                self._format_hidden(
                    start,
                    mark_len,
                )

                self._format_text(
                    start + mark_len,
                    content_len,
                    color,
                    bold=bold,
                    italic=italic,
                    strike=strike,
                    bg=bg,
                )

                self._format_hidden(
                    end - mark_len,
                    mark_len,
                )


class ObsidianMarkdownEditor(QTextEdit):
    """Editor Markdown con estilo propio independiente del CSS global."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Estilo propio del editor.
        # Esto evita que dependa de que style.css se haya cargado
        # correctamente o de que otro selector lo sobrescriba.
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
                selection-color: #f5e0dc;
                border: none;
                padding: 18px;
                font-family: "Consolas", "Fira Code", "Courier New", monospace;
                font-size: 14px;
            }

            QScrollBar:vertical {
                background: #1e1e2e;
                width: 8px;
                border: none;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: #45475a;
                min-height: 20px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background: #585b70;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.highlighter = MarkdownLiveHighlighter(self.document())

        self.cursorPositionChanged.connect(self.on_cursor_changed)

        # Primera posición: bloque activo para que al hacer clic/escribir
        # inmediatamente se comporte como editor Markdown.
        self.on_cursor_changed()

    def on_cursor_changed(self):
        cursor = self.textCursor()
        block_number = cursor.block().blockNumber()
        self.highlighter.set_active_block(block_number)
