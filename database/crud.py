from sqlalchemy.orm import Session
from . import models


# ─── Condominiums ───────────────────────────────────────────────────────────

def create_condominium(db: Session, rif: str, name: str) -> models.Condominium:
    obj = models.Condominium(rif=rif.strip(), name=name.strip())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_condominiums(db: Session):
    return db.query(models.Condominium).order_by(models.Condominium.name).all()

def get_condominium(db: Session, condo_id: int) -> models.Condominium | None:
    return db.query(models.Condominium).filter(models.Condominium.id == condo_id).first()

def update_condominium(db: Session, condo_id: int, rif: str, name: str) -> models.Condominium | None:
    obj = get_condominium(db, condo_id)
    if obj:
        obj.rif = rif.strip()
        obj.name = name.strip()
        db.commit()
        db.refresh(obj)
    return obj

def delete_condominium(db: Session, condo_id: int) -> bool:
    obj = get_condominium(db, condo_id)
    if obj:
        db.delete(obj)
        db.commit()
        return True
    return False


# ─── Clients ────────────────────────────────────────────────────────────────

def create_client(db: Session, name: str, cedula_rif: str, phone: str,
                  account_numbers: str, condo_id: int,
                  property_code: str = "", email: str = "",
                  keywords: str = "") -> models.Client:
    obj = models.Client(
        property_code=property_code.strip(),
        name=name.strip(), cedula_rif=cedula_rif.strip(),
        phone=phone.strip(), email=email.strip(),
        keywords=keywords.strip(),
        account_numbers=account_numbers.strip(),
        condominium_id=condo_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_clients(db: Session, condo_id: int):
    return (db.query(models.Client)
              .filter(models.Client.condominium_id == condo_id)
              .order_by(models.Client.name)
              .all())

def get_client(db: Session, client_id: int) -> models.Client | None:
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def update_client(db: Session, client_id: int, name: str, cedula_rif: str,
                  phone: str, account_numbers: str,
                  property_code: str = "", email: str = "",
                  keywords: str = "") -> models.Client | None:
    obj = get_client(db, client_id)
    if obj:
        obj.property_code = property_code.strip()
        obj.name = name.strip()
        obj.cedula_rif = cedula_rif.strip()
        obj.phone = phone.strip()
        obj.email = email.strip()
        obj.keywords = keywords.strip()
        obj.account_numbers = account_numbers.strip()
        db.commit()
        db.refresh(obj)
    return obj

def delete_client(db: Session, client_id: int) -> bool:
    obj = get_client(db, client_id)
    if obj:
        db.delete(obj)
        db.commit()
        return True
    return False

def search_clients(db: Session, condo_id: int, query: str):
    q = f"%{query.lower()}%"
    return (db.query(models.Client)
              .filter(models.Client.condominium_id == condo_id)
              .filter(
                  models.Client.name.ilike(q) |
                  models.Client.cedula_rif.ilike(q) |
                  models.Client.phone.ilike(q) |
                  models.Client.account_numbers.ilike(q) |
                  models.Client.property_code.ilike(q) |
                  models.Client.email.ilike(q) |
                  models.Client.keywords.ilike(q)
              )
              .order_by(models.Client.name)
              .all())


# ─── Suppliers ──────────────────────────────────────────────────────────────

def create_supplier(db: Session, name: str, cedula_rif: str, phone: str,
                    account_numbers: str, condo_id: int) -> models.Supplier:
    obj = models.Supplier(
        name=name.strip(), cedula_rif=cedula_rif.strip(),
        phone=phone.strip(), account_numbers=account_numbers.strip(),
        condominium_id=condo_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_suppliers(db: Session, condo_id: int):
    return (db.query(models.Supplier)
              .filter(models.Supplier.condominium_id == condo_id)
              .order_by(models.Supplier.name)
              .all())

def get_supplier(db: Session, supplier_id: int) -> models.Supplier | None:
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()

def update_supplier(db: Session, supplier_id: int, name: str, cedula_rif: str,
                    phone: str, account_numbers: str) -> models.Supplier | None:
    obj = get_supplier(db, supplier_id)
    if obj:
        obj.name = name.strip()
        obj.cedula_rif = cedula_rif.strip()
        obj.phone = phone.strip()
        obj.account_numbers = account_numbers.strip()
        db.commit()
        db.refresh(obj)
    return obj

def delete_supplier(db: Session, supplier_id: int) -> bool:
    obj = get_supplier(db, supplier_id)
    if obj:
        db.delete(obj)
        db.commit()
        return True
    return False

def search_suppliers(db: Session, condo_id: int, query: str):
    q = f"%{query.lower()}%"
    return (db.query(models.Supplier)
              .filter(models.Supplier.condominium_id == condo_id)
              .filter(
                  models.Supplier.name.ilike(q) |
                  models.Supplier.cedula_rif.ilike(q) |
                  models.Supplier.account_numbers.ilike(q)
              )
              .order_by(models.Supplier.name)
              .all())


# ─── Transactions ────────────────────────────────────────────────────────────

def create_transaction(db: Session, date, reference: str, description: str,
                       amount: float, t_type: models.TransactionType,
                       condo_id: int) -> models.Transaction:
    obj = models.Transaction(
        date=date, reference=reference, description=description,
        amount=amount, transaction_type=t_type,
        status=models.TransactionStatus.SIN_CONCILIAR,
        condominium_id=condo_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def create_transactions_bulk(db: Session, transactions: list[dict], condo_id: int):
    objs = [models.Transaction(**t, condominium_id=condo_id) for t in transactions]
    db.bulk_save_objects(objs)
    db.commit()

def get_transactions(db: Session, condo_id: int, start_date=None, end_date=None):
    query = db.query(models.Transaction).filter(models.Transaction.condominium_id == condo_id)
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    return query.order_by(models.Transaction.date.desc()).all()

def update_transaction(db: Session, transaction_id: int,
                       status: models.TransactionStatus | None = None,
                       status_note: str | None = None,
                       client_id: int | None = None,
                       supplier_id: int | None = None) -> models.Transaction | None:
    obj = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if obj:
        if status is not None:
            obj.status = status
        if status_note is not None:
            obj.status_note = status_note[:25]
        if client_id is not None:
            obj.client_id = client_id
            obj.supplier_id = None
        if supplier_id is not None:
            obj.supplier_id = supplier_id
            obj.client_id = None
        db.commit()
        db.refresh(obj)
    return obj
