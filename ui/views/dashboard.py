from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CardWidget, FluentIcon, IconWidget
)
from database import crud
from database.models import TransactionStatus, TransactionType
from ui.db_session import db_session


class StatCard(CardWidget):
    def __init__(self, title: str, value: str = "0", icon=None, color="#5b6af0", parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        if icon:
            ico = IconWidget(icon, self)
            ico.setFixedSize(32, 32)
            layout.addWidget(ico)

        text_col = QVBoxLayout()
        self.value_lbl = SubtitleLabel(value, self)
        self.value_lbl.setStyleSheet(f"color:{color}; font-weight:700; font-size:20px;")
        self.title_lbl = BodyLabel(title, self)
        self.title_lbl.setTextColor("#777", "#aaa")
        text_col.addWidget(self.value_lbl)
        text_col.addWidget(self.title_lbl)
        layout.addLayout(text_col)
        layout.addStretch(1)

    def update_value(self, val: str):
        self.value_lbl.setText(val)


class DashboardInterface(QWidget):
    def __init__(self, condo_id_getter, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DashboardInterface")
        self.get_condo_id = condo_id_getter
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(24)

        # Header Row
        hdr = QHBoxLayout()
        title_col = QVBoxLayout()
        self.title    = TitleLabel("Panel Principal", self)
        self.subtitle = BodyLabel(
            "Selecciona un condominio en la barra de navegación para ver el resumen.", self
        )
        self.subtitle.setTextColor("#888", "#aaa")
        self.subtitle.setFixedHeight(20) # Fijar altura para evitar saltos
        title_col.addWidget(self.title)
        title_col.addWidget(self.subtitle)
        hdr.addLayout(title_col)
        hdr.addStretch(1)

        # Date Filter
        from qfluentwidgets import ComboBox, CalendarPicker
        filter_layout = QHBoxLayout()
        filter_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        filter_layout.addWidget(BodyLabel("Período:", self))
        self.period_combo = ComboBox(self)
        self.period_combo.addItems(["Este Mes", "Mes Pasado", "Personalizado", "Histórico Completo"])
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        filter_layout.addWidget(self.period_combo)
        
        self.start_cal = CalendarPicker(self)
        self.end_cal = CalendarPicker(self)
        self.start_cal.dateChanged.connect(self.refresh)
        self.end_cal.dateChanged.connect(self.refresh)
        
        self.start_cal.setVisible(False)
        self.end_cal.setVisible(False)
        
        filter_layout.addWidget(self.start_cal)
        filter_layout.addWidget(self.end_cal)

        hdr.addLayout(filter_layout)
        root.addLayout(hdr)

        # Stats grid 3×2
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_tx      = StatCard("Total Transacciones", "0",       FluentIcon.DOCUMENT,     "#5b6af0", self)
        self.card_abonos  = StatCard("Total Abonos",        "Bs 0,00", FluentIcon.ACCEPT,       "#1e8449", self)
        self.card_cargos  = StatCard("Total Cargos",        "Bs 0,00", FluentIcon.CANCEL,       "#c0392b", self)
        self.card_sin     = StatCard("Sin Conciliar",        "0",       FluentIcon.HISTORY,      "#e67e22", self)
        self.card_clients = StatCard("Clientes Registrados", "0",       FluentIcon.PEOPLE,       "#5b6af0", self)
        self.card_suppl   = StatCard("Proveedores",          "0",       FluentIcon.SHOPPING_CART,"#8e44ad", self)

        grid.addWidget(self.card_tx,      0, 0)
        grid.addWidget(self.card_abonos,  0, 1)
        grid.addWidget(self.card_cargos,  0, 2)
        grid.addWidget(self.card_sin,     1, 0)
        grid.addWidget(self.card_clients, 1, 1)
        grid.addWidget(self.card_suppl,   1, 2)
        root.addLayout(grid)
        root.addStretch(1)

    def _on_period_changed(self):
        is_custom = self.period_combo.currentText() == "Personalizado"
        self.start_cal.setVisible(is_custom)
        self.end_cal.setVisible(is_custom)
        self.refresh()

    def refresh(self):
        condo_id = self.get_condo_id()
        if not condo_id:
            for card in [self.card_tx, self.card_abonos, self.card_cargos,
                         self.card_sin, self.card_clients, self.card_suppl]:
                card.update_value("—")
            self.subtitle.setText(
                "Selecciona un condominio en la barra de navegación para ver el resumen."
            )
            return

        import datetime
        from dateutil.relativedelta import relativedelta
        today = datetime.date.today()
        start_date = None
        end_date = None

        period = self.period_combo.currentText()
        if period == "Este Mes":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "Mes Pasado":
            start_date = (today.replace(day=1) - relativedelta(months=1))
            end_date = today.replace(day=1) - datetime.timedelta(days=1)
        elif period == "Personalizado":
            # CalendarPicker devuelve un QDate
            q_start = self.start_cal.getDate()
            q_end = self.end_cal.getDate()
            if q_start.isValid() and q_end.isValid():
                start_date = q_start.toPyDate()
                end_date = q_end.toPyDate()

        txs     = crud.get_transactions(db_session, condo_id, start_date=start_date, end_date=end_date)
        clients = crud.get_clients(db_session, condo_id)
        suppl   = crud.get_suppliers(db_session, condo_id)

        total_ab = sum(t.amount or 0 for t in txs if t.transaction_type == TransactionType.ABONO)
        total_ca = sum(t.amount or 0 for t in txs if t.transaction_type == TransactionType.CARGO)
        sin_count = sum(1 for t in txs if t.status == TransactionStatus.SIN_CONCILIAR)

        self.card_tx.update_value(str(len(txs)))
        self.card_abonos.update_value(f"Bs {total_ab:,.2f}")
        self.card_cargos.update_value(f"Bs {total_ca:,.2f}")
        self.card_sin.update_value(str(sin_count))
        self.card_clients.update_value(str(len(clients)))
        self.card_suppl.update_value(str(len(suppl)))
        
        lbl = f"Estadísticas del condominio activo ({period})."
        if period != "Histórico Completo" and start_date and end_date:
            lbl += f" [{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}]"
        self.subtitle.setText(lbl)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
