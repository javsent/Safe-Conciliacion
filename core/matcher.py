import re
from typing import List, Optional, Tuple
from database import models
from sqlalchemy.orm import Session

class SmartMatcher:
    def __init__(self, db: Session, condo_id: int):
        self.db = db
        self.condo_id = condo_id
        
        # Load clients and suppliers into memory for fast matching
        self.clients = self.db.query(models.Client).filter(models.Client.condominium_id == condo_id).all()
        self.suppliers = self.db.query(models.Supplier).filter(models.Supplier.condominium_id == condo_id).all()
        
    def find_match(self, description: str, t_type: models.TransactionType) -> Tuple[Optional[int], Optional[int]]:
        """
        Attempts to find a client (if ABONO) or supplier (if CARGO) based on description.
        Returns a tuple of (client_id, supplier_id). One of them will be None.
        """
        description = description.lower()
        
        if t_type == models.TransactionType.ABONO:
            for client in self.clients:
                # Check for cedula/rif
                if client.cedula_rif and client.cedula_rif.lower() in description:
                    return client.id, None
                # Check for account numbers
                if client.account_numbers:
                    for acc in client.account_numbers.split(','):
                        if acc.strip() in description:
                            return client.id, None
                # Check for name parts
                if client.name:
                    name_parts = client.name.lower().split()
                    if len(name_parts) >= 2 and all(part in description for part in name_parts):
                        return client.id, None
            return None, None
            
        elif t_type == models.TransactionType.CARGO:
            for supplier in self.suppliers:
                if supplier.cedula_rif and supplier.cedula_rif.lower() in description:
                    return None, supplier.id
                if supplier.account_numbers:
                    for acc in supplier.account_numbers.split(','):
                        if acc.strip() in description:
                            return None, supplier.id
                if supplier.name:
                    name_parts = supplier.name.lower().split()
                    if len(name_parts) >= 2 and all(part in description for part in name_parts):
                        return None, supplier.id
            return None, None
            
    def update_profile_from_manual_assignment(self, transaction: models.Transaction):
        """
        When a user manually assigns a transaction, extract useful info 
        and append it to the client/supplier profile to improve future matches.
        """
        pass
