"""
Diálogo de importación de estados de cuenta bancarios.
Soporta: Excel (.xlsx/.xls), CSV, TXT.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, PushButton, PrimaryPushButton,
    ComboBox, LineEdit, InfoBar, InfoBarPosition, FluentIcon
)
from core.parser_factory import ParserFactory
from database import crud
from database.models import TransactionType
from ui.db_session import db_session


BANKS = [
    "Banesco",
    "Mercantil",
    "Banco Provincial (BBVA)",
    "Banco Nacional de Crédito (BNC)",
    "Banco Exterior",
    "Banco Plaza",
    "Bancaribe",
    "Otro (Genérico)",
]


class ImportDialog(QDialog):
    def __init__(self, condo_id_getter, parent=None):
        super().__init__(parent)
        self.get_condo_id = condo_id_getter
        self.setWindowTitle("Importar Estado de Cuenta")
        self.setFixedWidth(540)
        self.setModal(True)
        self._file_path = None
        self._current_format = 'excel'
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        layout.addWidget(SubtitleLabel("Importar Estado de Cuenta Bancario", self))
        self.desc_label = BodyLabel(
            "Selecciona el formato, el banco y el archivo del estado de cuenta.", self
        )
        layout.addWidget(self.desc_label)

        # Formato selector
        from qfluentwidgets import SegmentedWidget
        self.format_pivot = SegmentedWidget(self)
        self.format_pivot.addItem('excel', 'Excel / CSV')
        self.format_pivot.addItem('pdf', 'Documento PDF')
        
        layout.addWidget(self.format_pivot, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Bank selector
        bank_row = QHBoxLayout()
        bank_row.addWidget(BodyLabel("Banco:", self))
        self.bank_combo = ComboBox(self)
        self.bank_combo.setMinimumWidth(280)
        bank_row.addWidget(self.bank_combo)
        bank_row.addStretch(1)
        layout.addLayout(bank_row)

        # File selector
        file_row = QHBoxLayout()
        self.file_label = LineEdit(self)
        self.file_label.setReadOnly(True)
        self.file_label.setPlaceholderText("Ningún archivo seleccionado...")
        browse_btn = PushButton(FluentIcon.FOLDER, "Examinar...", self)
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self.file_label)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # Status / preview
        self.preview_lbl = BodyLabel("", self)
        self.preview_lbl.setTextColor("#555", "#aaa")
        layout.addWidget(self.preview_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel = PushButton("Cancelar", self)
        cancel.clicked.connect(self.reject)
        self.import_btn = PrimaryPushButton("Importar", self)
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._do_import)
        btn_row.addWidget(cancel)
        btn_row.addWidget(self.import_btn)
        layout.addLayout(btn_row)

        self.format_pivot.currentItemChanged.connect(self._on_format_changed)
        self.format_pivot.setCurrentItem('excel')

    def _on_format_changed(self, format_key):
        self._current_format = format_key
        self.bank_combo.clear()
        if format_key == 'excel':
            self.bank_combo.addItems(BANKS)
            self.desc_label.setText("Formatos soportados: Excel (.xlsx, .xls), CSV, TXT.")
        elif format_key == 'pdf':
            self.bank_combo.addItems([
                "Banco Nacional de Crédito (BNC) (PDF)",
                "Banesco (PDF)",
                "Mercantil (PDF)",
                "Banco Provincial (BBVA) (PDF)"
                # Añadir más conforme se implementen
            ])
            self.desc_label.setText("Formatos soportados: Documentos PDF (.pdf).")
        
        # Reset file
        self._file_path = None
        self.file_label.clear()
        self.import_btn.setEnabled(False)
        self.preview_lbl.clear()

    def _browse(self):
        is_pdf = self._current_format == 'pdf'
        filter_str = "Documentos PDF (*.pdf)" if is_pdf else "Archivos soportados (*.xlsx *.xls *.csv *.txt);;Excel (*.xlsx *.xls);;CSV / TXT (*.csv *.txt)"
        
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Estado de Cuenta", "", filter_str
        )
        if path:
            self._file_path = path
            self.file_label.setText(path.split("/")[-1])
            self.import_btn.setEnabled(True)
            self.preview_lbl.setText(f"Archivo listo: {path}")

    def _do_import(self):
        condo_id = self.get_condo_id()
        if not condo_id:
            InfoBar.warning(
                title="Sin condominio activo",
                content="Selecciona un condominio antes de importar.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )
            return

        bank = self.bank_combo.currentText()
        parser = ParserFactory.get_parser(bank, self._file_path)

        try:
            df = parser.parse(self._file_path)
        except Exception as e:
            InfoBar.error(
                title="Error al leer el archivo",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )
            return

        if df is None or df.empty:
            InfoBar.error(
                title="Sin datos",
                content="No se encontraron transacciones en el archivo. "
                        "Verifica el formato o elige otro banco.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=4000,
            )
            return

        inserted = 0
        for _, row in df.iterrows():
            t_type = (
                TransactionType.ABONO
                if str(row.get("type", "")).upper() == "ABONO"
                else TransactionType.CARGO
            )
            try:
                crud.create_transaction(
                    db_session,
                    date=row.get("date"),
                    reference=str(row.get("reference", "") or ""),
                    description=str(row.get("description", "") or ""),
                    amount=float(row.get("amount", 0) or 0),
                    t_type=t_type,
                    condo_id=condo_id,
                )
                inserted += 1
            except Exception:
                continue

        self.preview_lbl.setText(f"✔ {inserted} transacciones importadas.")
        self.import_btn.setEnabled(False)
        self.accept()
