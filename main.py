import sys
import os
import traceback

from PyQt6.QtWidgets import QApplication

from database.connection import engine, Base
from database import models


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    try:
        init_db()
        app = QApplication(sys.argv)
        
        # Forzar tema claro globalmente
        from qfluentwidgets import setTheme, Theme
        setTheme(Theme.LIGHT)
        
        # Aplicar estilo por defecto a los QDialog para arreglar el contraste
        app.setStyleSheet("QDialog { background-color: #ffffff; }")

        # Import MainWindow AFTER QApplication is created
        from ui.main_window import MainWindow

        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        with open("crash.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"Error fatal: {e}")
        traceback.print_exc()
