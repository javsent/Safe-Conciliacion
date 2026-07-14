"""
Singleton de sesión de base de datos compartido por toda la UI.
Importa `db_session` desde este módulo en cualquier vista.
"""
from database.connection import SessionLocal

db_session = SessionLocal()
