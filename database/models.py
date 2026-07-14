from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .connection import Base
import enum

class TransactionStatus(enum.Enum):
    CONCILIADO = "Conciliado"
    SIN_CONCILIAR = "Sin Conciliar"
    OTRO = "Otro"

class TransactionType(enum.Enum):
    ABONO = "Abono"
    CARGO = "Cargo"

class Condominium(Base):
    __tablename__ = "condominiums"
    
    id = Column(Integer, primary_key=True, index=True)
    rif = Column(String, index=True)
    name = Column(String, index=True)
    
    clients = relationship("Client", back_populates="condominium")
    suppliers = relationship("Supplier", back_populates="condominium")
    transactions = relationship("Transaction", back_populates="condominium")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    property_code = Column(String, index=True)  # Ej: 16-A
    name = Column(String, index=True)
    cedula_rif = Column(String, index=True)
    phone = Column(String)
    email = Column(String)
    keywords = Column(String)  # Separadas por ; para búsqueda inteligente
    account_numbers = Column(String) # Comma separated or JSON string
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="clients")
    
    transactions = relationship("Transaction", back_populates="client")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cedula_rif = Column(String, index=True)
    phone = Column(String)
    account_numbers = Column(String) # Comma separated or JSON string
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="suppliers")
    
    transactions = relationship("Transaction", back_populates="supplier")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    reference = Column(String, index=True)
    description = Column(String)
    amount = Column(Float)
    transaction_type = Column(Enum(TransactionType))
    status = Column(Enum(TransactionStatus), default=TransactionStatus.SIN_CONCILIAR)
    status_note = Column(String(25)) # For 'OTRO' 25 chars
    
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client = relationship("Client", back_populates="transactions")
    
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier = relationship("Supplier", back_populates="transactions")
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="transactions")
