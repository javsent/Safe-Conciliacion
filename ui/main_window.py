from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    BodyLabel, NavigationAvatarWidget, RoundMenu, Action
)
from database import crud
from ui.db_session import db_session
from ui.views.condominium_view import CondominiumDialog


class MainWindow(FluentWindow):
    condo_changed = pyqtSignal(int)   # emitted when active condo changes

    def __init__(self):
        super().__init__()
        self._active_condo_id = None
        self._init_views()
        self._init_window()
        self._init_navigation()
        self._init_condo_selector()
        self.refresh_condo_selector()

    # ── Setup ─────────────────────────────────────────────────────────────────
    def _init_views(self):
        """Create views (must happen before navigation is set up)."""
        from ui.views.dashboard import DashboardInterface
        from ui.views.condominium_view import CondominiumInterface
        from ui.views.entities_view import EntitiesInterface
        from ui.views.conciliation_view import ConciliationInterface

        self.dashboardInterface    = DashboardInterface(self.get_active_condo_id, self)
        self.condominiumInterface  = CondominiumInterface(self)
        self.entitiesInterface     = EntitiesInterface(self.get_active_condo_id, self)
        self.conciliationInterface = ConciliationInterface(self.get_active_condo_id, self)

    def _init_window(self):
        self.resize(1280, 820)
        self.setWindowTitle('Safe Conciliación')
        desktop = self.screen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def _init_navigation(self):
        self.addSubInterface(self.dashboardInterface,    FluentIcon.HOME,          'Inicio')
        self.addSubInterface(self.condominiumInterface,  FluentIcon.FOLDER,        'Gestionar Condominios')
        self.addSubInterface(self.entitiesInterface,     FluentIcon.PEOPLE,        'Entidades')
        self.addSubInterface(self.conciliationInterface, FluentIcon.DOCUMENT,      'Conciliación')

    def _init_condo_selector(self):
        """Añadir un widget de avatar en la parte inferior para seleccionar el condominio activo."""
        self.avatarWidget = NavigationAvatarWidget('Sin Condominio', 'resources/default_avatar.png')
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=self.avatarWidget,
            onClick=self._show_condo_menu,
            position=NavigationItemPosition.BOTTOM
        )

    def _show_condo_menu(self):
        menu = RoundMenu(parent=self)
        
        # Añadir opción de agregar nuevo
        add_action = Action(FluentIcon.ADD, "Agregar nuevo...", self)
        add_action.triggered.connect(self._add_new_condo)
        menu.addAction(add_action)
        menu.addSeparator()

        # Listar condominios existentes
        condos = crud.get_condominiums(db_session)
        for c in condos:
            # Crear accion, si es el activo le ponemos un check
            act = Action(FluentIcon.ACCEPT if c.id == self._active_condo_id else FluentIcon.FOLDER, c.name, self)
            act.triggered.connect(lambda checked, cid=c.id, cname=c.name: self._on_condo_changed(cid, cname))
            menu.addAction(act)
            
        # Mostrar menú encima del avatar
        pos = self.avatarWidget.mapToGlobal(self.avatarWidget.rect().topLeft())
        # Ajustamos un poco la posicion para que salga encima
        menu.exec(pos)

    def _add_new_condo(self):
        dlg = CondominiumDialog(self)
        if dlg.exec():
            rif, name = dlg.get_data()
            if name:
                new_c = crud.create_condominium(db_session, rif, name)
                self.refresh_condo_selector()
                self._on_condo_changed(new_c.id, new_c.name)
                # Refrescar la tabla en CondominiumInterface
                if hasattr(self.condominiumInterface, '_load_data'):
                    self.condominiumInterface._load_data()

    # ── Condo logic ───────────────────────────────────────────────────────────
    def refresh_condo_selector(self):
        # Actualizar nombre si ya hay uno seleccionado
        if self._active_condo_id:
            c = crud.get_condominium(db_session, self._active_condo_id)
            if c:
                self.avatarWidget.setName(c.name)
            else:
                self._active_condo_id = None
                self.avatarWidget.setName('Seleccionar Condominio')
        else:
            self.avatarWidget.setName('Seleccionar Condominio')

    def _on_condo_changed(self, cid, cname):
        self._active_condo_id = cid
        self.avatarWidget.setName(cname)
        # Refresh all views
        self.dashboardInterface.refresh()
        if hasattr(self.entitiesInterface, 'refresh'):
            self.entitiesInterface.refresh()
        if hasattr(self.conciliationInterface, 'refresh'):
            self.conciliationInterface.refresh()

    def get_active_condo_id(self):
        return self._active_condo_id


