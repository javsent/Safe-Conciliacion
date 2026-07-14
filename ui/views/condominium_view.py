from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
    QAbstractItemView, QDialog, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, TableWidget, PushButton,
    LineEdit, PrimaryPushButton, MessageBox, FluentIcon,
    CardWidget, BodyLabel
)
from database import crud
from ui.db_session import db_session


class CondominiumDialog(QDialog):
    """Dialogo para crear o editar un Condominio/Comercio."""

    def __init__(self, parent=None, condominium=None):
        super().__init__(parent)
        self.condominium = condominium
        self.setWindowTitle("Agregar Condominio" if not condominium else "Editar Condominio")
        self.setFixedWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = SubtitleLabel(
            "Nuevo Condominio / Comercio" if not condominium else "Editar Condominio / Comercio",
            self
        )
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.rif_input = LineEdit(self)
        self.rif_input.setPlaceholderText("Ej: J-12345678-9")
        form.addRow("RIF:", self.rif_input)

        self.name_input = LineEdit(self)
        self.name_input.setPlaceholderText("Ej: Residencias Las Palmas")
        form.addRow("Razón Social:", self.name_input)

        layout.addLayout(form)

        if condominium:
            self.rif_input.setText(condominium.rif or "")
            self.name_input.setText(condominium.name or "")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        cancel_btn = PushButton("Cancelar", self)
        cancel_btn.clicked.connect(self.reject)
        save_btn = PrimaryPushButton("Guardar", self)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return self.rif_input.text().strip(), self.name_input.text().strip()


class CondominiumInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("CondominiumInterface")
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = TitleLabel("Condominios y Comercios", self)
        header.addWidget(title)
        header.addStretch(1)
        self.add_btn = PrimaryPushButton(FluentIcon.ADD, "Agregar", self)
        self.add_btn.clicked.connect(self._on_add)
        header.addWidget(self.add_btn)
        root.addLayout(header)

        hint = BodyLabel("Selecciona un condominio para activarlo como contexto de trabajo.", self)
        hint.setTextColor("#888", "#aaa")
        root.addWidget(hint)

        # Table
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "RIF", "Razón Social", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        condos = crud.get_condominiums(db_session)
        for row, condo in enumerate(condos):
            self.table.insertRow(row)
            from PyQt6.QtWidgets import QTableWidgetItem
            self.table.setItem(row, 0, QTableWidgetItem(str(condo.id)))
            self.table.setItem(row, 1, QTableWidgetItem(condo.rif or ""))
            self.table.setItem(row, 2, QTableWidgetItem(condo.name or ""))

            # Actions cell
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            edit_btn = PushButton(FluentIcon.EDIT, "", btn_widget)
            edit_btn.setFixedWidth(36)
            edit_btn.setToolTip("Editar")
            edit_btn.clicked.connect(lambda _, c=condo: self._on_edit(c))

            del_btn = PushButton(FluentIcon.DELETE, "", btn_widget)
            del_btn.setFixedWidth(36)
            del_btn.setToolTip("Eliminar")
            del_btn.clicked.connect(lambda _, c=condo: self._on_delete(c))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch(1)
            self.table.setCellWidget(row, 3, btn_widget)

    def _on_add(self):
        dlg = CondominiumDialog(self)
        if dlg.exec():
            rif, name = dlg.get_data()
            if not name:
                return
            crud.create_condominium(db_session, rif, name)
            self._load_data()

    def _on_edit(self, condo):
        dlg = CondominiumDialog(self, condominium=condo)
        if dlg.exec():
            rif, name = dlg.get_data()
            if not name:
                return
            crud.update_condominium(db_session, condo.id, rif, name)
            self._load_data()
            # Notify main window to refresh selector
            mw = self.window()
            if hasattr(mw, 'refresh_condo_selector'):
                mw.refresh_condo_selector()

    def _on_delete(self, condo):
        msg = MessageBox(
            "Confirmar eliminación",
            f"¿Eliminar '{condo.name}'?\nEsto eliminará también todos sus clientes, proveedores y transacciones.",
            self
        )
        if msg.exec():
            crud.delete_condominium(db_session, condo.id)
            self._load_data()
            mw = self.window()
            if hasattr(mw, 'refresh_condo_selector'):
                mw.refresh_condo_selector()
