from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
    QAbstractItemView, QTableWidgetItem, QDialog,
    QPushButton, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from qfluentwidgets import (
    TitleLabel, TableWidget, PushButton, PrimaryPushButton, ComboBox,
    LineEdit, FluentIcon, InfoBar, InfoBarPosition, MessageBox,
    SubtitleLabel, BodyLabel, SearchLineEdit, CardWidget
)
from database import crud
from database.models import TransactionStatus, TransactionType
from ui.db_session import db_session


# ─── Status display ──────────────────────────────────────────────────────────
STATUS_COLORS = {
    TransactionStatus.CONCILIADO:    ("#d4edda", "#155724"),
    TransactionStatus.SIN_CONCILIAR: ("#fff3cd", "#856404"),
    TransactionStatus.OTRO:          ("#cce5ff", "#004085"),
}
STATUS_LABELS = {
    TransactionStatus.CONCILIADO:    "Conciliado",
    TransactionStatus.SIN_CONCILIAR: "Sin Conciliar",
    TransactionStatus.OTRO:          "Otro",
}
STATUS_CYCLE = [
    TransactionStatus.SIN_CONCILIAR,
    TransactionStatus.CONCILIADO,
    TransactionStatus.OTRO,
]


# ─── Entity dropdown ─────────────────────────────────────────────────────────
class SearchableEntityCombo(QWidget):
    entity_selected = pyqtSignal(int, str)

    def __init__(self, entities: list, parent=None):
        super().__init__(parent)
        self._entities = entities
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)

        self.combo = ComboBox(self)
        self.combo.setMinimumWidth(180)
        self.combo.addItem("-- Sin asignar --", userData=None)
        for eid, ename in entities:
            self.combo.addItem(ename, userData=eid)
        self.combo.currentIndexChanged.connect(self._on_change)
        layout.addWidget(self.combo)

    def set_selected(self, entity_id):
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == entity_id:
                self.combo.setCurrentIndex(i)
                return

    def _on_change(self, index):
        eid = self.combo.itemData(index)
        if eid is not None:
            ename = self.combo.itemText(index)
            self.entity_selected.emit(eid, ename)

    def get_selected_id(self):
        return self.combo.currentData()


# ─── 'Otro' note dialog ──────────────────────────────────────────────────────
class OtroNoteDialog(QDialog):
    def __init__(self, current_note="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Descripción — Otro")
        self.setFixedWidth(380)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(SubtitleLabel("Descripción breve (máx. 25 caracteres)", self))
        self.note_input = LineEdit(self)
        self.note_input.setMaxLength(25)
        self.note_input.setPlaceholderText("Ej: Transferencia interna")
        self.note_input.setText(current_note)
        layout.addWidget(self.note_input)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel = PushButton("Cancelar", self)
        cancel.clicked.connect(self.reject)
        ok = PrimaryPushButton("Aceptar", self)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

    def get_note(self):
        return self.note_input.text().strip()


# ─── Transaction row manager ─────────────────────────────────────────────────
class TransactionRow:
    def __init__(self, table: TableWidget, row: int, transaction, entities: list, entity_type: str):
        self.table = table
        self.row = row
        self.tx = transaction
        self.entities = entities
        self.entity_type = entity_type
        self._render()

    def _set(self, col, text, align=Qt.AlignmentFlag.AlignVCenter):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(align)
        self.table.setItem(self.row, col, item)

    def _render(self):
        tx = self.tx
        date_str = tx.date.strftime("%d/%m/%Y") if tx.date else ""
        self._set(0, date_str)
        self._set(1, tx.reference or "")
        self._set(2, tx.description or "")

        # Amount
        amount_str = f"Bs {tx.amount:,.2f}" if tx.amount else "Bs 0,00"
        item = QTableWidgetItem(amount_str)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        color = "#1e8449" if tx.transaction_type == TransactionType.ABONO else "#c0392b"
        item.setForeground(QColor(color))
        self.table.setItem(self.row, 3, item)

        # Type badge
        type_label = "▲ Abono" if tx.transaction_type == TransactionType.ABONO else "▼ Cargo"
        badge = QLabel(type_label)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:{color}22; color:{color}; border-radius:8px;"
            f"padding:2px 10px; font-weight:600;"
        )
        self.table.setCellWidget(self.row, 4, badge)

        # Entity dropdown
        self.entity_combo = SearchableEntityCombo(self.entities, self.table)
        assigned = tx.client_id if self.entity_type == "client" else tx.supplier_id
        if assigned:
            self.entity_combo.set_selected(assigned)
        self.entity_combo.entity_selected.connect(self._on_entity_selected)
        self.table.setCellWidget(self.row, 5, self.entity_combo)

        # Status button
        self._render_status_btn()

    def _render_status_btn(self):
        status = self.tx.status or TransactionStatus.SIN_CONCILIAR
        bg, fg = STATUS_COLORS[status]
        if status == TransactionStatus.OTRO and self.tx.status_note:
            label = f"{self.tx.status_note}"
        else:
            label = STATUS_LABELS[status]

        btn = QPushButton(label)
        btn.setStyleSheet(
            f"QPushButton {{ background:{bg}; color:{fg}; border:1px solid {fg}55;"
            f"border-radius:8px; padding:6px 12px; font-weight:600; min-width:130px; }}"
            f"QPushButton:hover {{ background:{fg}22; }}"
        )
        btn.clicked.connect(self._cycle_status)
        self.table.setCellWidget(self.row, 6, btn)

    def _cycle_status(self):
        current = self.tx.status or TransactionStatus.SIN_CONCILIAR
        idx = STATUS_CYCLE.index(current)
        next_status = STATUS_CYCLE[(idx + 1) % len(STATUS_CYCLE)]
        note = self.tx.status_note

        if next_status == TransactionStatus.OTRO:
            dlg = OtroNoteDialog(note or "", self.table)
            if not dlg.exec():
                return
            note = dlg.get_note()

        crud.update_transaction(db_session, self.tx.id, status=next_status, status_note=note)
        self.tx.status = next_status
        self.tx.status_note = note
        self._render_status_btn()

    def _on_entity_selected(self, eid, ename):
        if self.entity_type == "client":
            crud.update_transaction(db_session, self.tx.id, client_id=eid)
        else:
            crud.update_transaction(db_session, self.tx.id, supplier_id=eid)
        InfoBar.success(
            title="Asignado",
            content=f"Asignado a: {ename}",
            parent=self.table.window(),
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
        )


# ─── Summary card ─────────────────────────────────────────────────────────────
class SummaryCard(CardWidget):
    def __init__(self, title: str, value: str = "0", color: str = "#5b6af0", parent=None):
        super().__init__(parent)
        self.setFixedHeight(76)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        self.lbl_title = BodyLabel(title, self)
        self.lbl_title.setTextColor("#888", "#aaa")
        self.lbl_value = SubtitleLabel(value, self)
        self.lbl_value.setStyleSheet(f"color:{color}; font-weight:700;")
        layout.addWidget(self.lbl_value)
        layout.addWidget(self.lbl_title)

    def update_value(self, val: str):
        self.lbl_value.setText(val)


# ─── Main conciliation view ───────────────────────────────────────────────────
class ConciliationInterface(QWidget):
    def __init__(self, condo_id_getter, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ConciliationInterface")
        self.get_condo_id = condo_id_getter
        self._all_transactions = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(TitleLabel("Conciliación Bancaria", self))
        hdr.addStretch(1)
        
        # Mover search_box aquí (arriba a la derecha)
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("Buscar por palabra clave...")
        self.search_box.setMinimumWidth(260)
        self.search_box.textChanged.connect(self._apply_filters)
        hdr.addWidget(self.search_box)
        
        self.load_btn = PrimaryPushButton(FluentIcon.FOLDER, "Cargar Estado de Cuenta", self)
        self.load_btn.clicked.connect(self._on_load)
        hdr.addWidget(self.load_btn)
        root.addLayout(hdr)

        # Filters
        filt = QHBoxLayout()
        filt.setSpacing(10)
        filt.addWidget(BodyLabel("Tipo:", self))
        self.filter_type = ComboBox(self)
        self.filter_type.addItems(["Todos", "Abonos", "Cargos"])
        self.filter_type.setMinimumWidth(110)
        self.filter_type.currentIndexChanged.connect(self._apply_filters)
        filt.addWidget(self.filter_type)

        filt.addWidget(BodyLabel("Estatus:", self))
        self.filter_status = ComboBox(self)
        self.filter_status.addItems(["Todos", "Sin Conciliar", "Conciliado", "Otro"])
        self.filter_status.setMinimumWidth(140)
        self.filter_status.currentIndexChanged.connect(self._apply_filters)
        filt.addWidget(self.filter_status)
        filt.addStretch(1)
        root.addLayout(filt)

        # Summary cards
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_total  = SummaryCard("Total Transacciones", "0",      "#5b6af0", self)
        self.card_abonos = SummaryCard("Total Abonos",  "Bs 0,00",      "#1e8449", self)
        self.card_cargos = SummaryCard("Total Cargos",  "Bs 0,00",      "#c0392b", self)
        self.card_sin    = SummaryCard("Sin Conciliar", "0",             "#e67e22", self)
        cards.addWidget(self.card_total)
        cards.addWidget(self.card_abonos)
        cards.addWidget(self.card_cargos)
        cards.addWidget(self.card_sin)
        root.addLayout(cards)

        # Table
        self.table = TableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Referencia", "Descripción", "Monto", "Tipo", "Asignado a", "Estatus"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        for col in (0, 1, 3, 4, 6):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

    # ── Data ─────────────────────────────────────────────────────────────────
    def _get_entities(self, t_type):
        cid = self.get_condo_id()
        if not cid:
            return []
        if t_type == TransactionType.ABONO:
            return [(c.id, c.name) for c in crud.get_clients(db_session, cid)]
        return [(s.id, s.name) for s in crud.get_suppliers(db_session, cid)]

    def _populate_table(self, transactions):
        self.table.setRowCount(0)
        self.table.setRowCount(len(transactions))
        for row, tx in enumerate(transactions):
            etype = "client" if tx.transaction_type == TransactionType.ABONO else "supplier"
            TransactionRow(self.table, row, tx, self._get_entities(tx.transaction_type), etype)
        self.table.resizeRowsToContents()
        # Update cards
        abonos = [t for t in transactions if t.transaction_type == TransactionType.ABONO]
        cargos = [t for t in transactions if t.transaction_type == TransactionType.CARGO]
        sin    = [t for t in transactions if t.status == TransactionStatus.SIN_CONCILIAR]
        self.card_total.update_value(str(len(transactions)))
        self.card_abonos.update_value(f"Bs {sum(t.amount or 0 for t in abonos):,.2f}")
        self.card_cargos.update_value(f"Bs {sum(t.amount or 0 for t in cargos):,.2f}")
        self.card_sin.update_value(str(len(sin)))

    def _apply_filters(self):
        ti = self.filter_type.currentIndex()
        si = self.filter_status.currentIndex()
        q  = self.search_box.text().strip().lower()
        txs = self._all_transactions
        if ti == 1: txs = [t for t in txs if t.transaction_type == TransactionType.ABONO]
        elif ti == 2: txs = [t for t in txs if t.transaction_type == TransactionType.CARGO]
        if si == 1: txs = [t for t in txs if t.status == TransactionStatus.SIN_CONCILIAR]
        elif si == 2: txs = [t for t in txs if t.status == TransactionStatus.CONCILIADO]
        elif si == 3: txs = [t for t in txs if t.status == TransactionStatus.OTRO]
        if q:
            txs = [t for t in txs if q in (t.reference or "").lower() or q in (t.description or "").lower()]
        self._populate_table(txs)

    def refresh(self):
        cid = self.get_condo_id()
        if not cid:
            self.table.setRowCount(0)
            return
        self._all_transactions = crud.get_transactions(db_session, cid)
        self._apply_filters()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def _on_load(self):
        from ui.views.import_dialog import ImportDialog
        dlg = ImportDialog(self.get_condo_id, self)
        if dlg.exec():
            self.refresh()
            InfoBar.success(
                title="Importación completada",
                content="Transacciones cargadas correctamente.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )
