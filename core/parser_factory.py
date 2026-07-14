"""
Parser Factory — selecciona el parser correcto según banco y tipo de archivo.
Todos los parsers devuelven un DataFrame estandarizado con columnas:
    date (datetime.date), reference (str), description (str),
    amount (float), type (str: "ABONO" | "CARGO")
"""
import pandas as pd
from pathlib import Path
from datetime import date


# ─── Base class ──────────────────────────────────────────────────────────────
class BaseParser:
    def parse(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError

    def _standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Asegura que el DataFrame tenga las columnas correctas."""
        required = ["date", "reference", "description", "amount", "type"]
        for col in required:
            if col not in df.columns:
                df[col] = None
        return df[required]


# ─── Generic Excel/CSV parser ─────────────────────────────────────────────────
class GenericExcelParser(BaseParser):
    """
    Parser genérico para Excel y CSV.
    Intenta mapear columnas comunes automáticamente.
    """
    COLUMN_MAP = {
        "date":        ["fecha", "date", "f_transaccion", "fech", "día", "dia"],
        "reference":   ["referencia", "ref", "reference", "nro", "numero", "num"],
        "description": ["descripcion", "descripción", "concepto", "detalle", "description", "movimiento"],
        "amount":      ["monto", "importe", "amount", "valor"],
        "credit":      ["abono", "credito", "crédito", "haber", "credit", "deposito", "depósito"],
        "debit":       ["cargo", "debito", "débito", "debe", "debit", "retiro"],
    }

    def parse(self, file_path: str) -> pd.DataFrame:
        ext = Path(file_path).suffix.lower()
        try:
            if ext in (".xlsx", ".xls"):
                raw = pd.read_excel(file_path, header=None)
            else:
                raw = pd.read_csv(file_path, sep=None, engine="python", header=None, encoding="utf-8-sig")
        except Exception as e:
            print(f"[Parser] Error leyendo archivo: {e}")
            return pd.DataFrame()

        # Find header row (first row with >2 non-null text cells)
        header_row = 0
        for i, row in raw.iterrows():
            non_null = row.dropna().astype(str).str.strip().str.len() > 0
            if non_null.sum() >= 3:
                header_row = i
                break

        raw.columns = raw.iloc[header_row].astype(str).str.strip().str.lower()
        raw = raw.iloc[header_row + 1:].reset_index(drop=True)
        raw = raw.dropna(how="all")

        # Map columns
        col_mapping = {}
        for target, candidates in self.COLUMN_MAP.items():
            for col in raw.columns:
                if any(c in col for c in candidates):
                    col_mapping[col] = target
                    break

        raw = raw.rename(columns=col_mapping)

        rows = []
        for _, r in raw.iterrows():
            credit = self._to_float(r.get("credit"))
            debit  = self._to_float(r.get("debit"))
            amount = self._to_float(r.get("amount"))

            if credit and credit > 0:
                amt  = credit
                ttype = "ABONO"
            elif debit and debit > 0:
                amt  = debit
                ttype = "CARGO"
            elif amount:
                amt  = abs(amount)
                ttype = "ABONO" if amount > 0 else "CARGO"
            else:
                continue

            rows.append({
                "date":        self._to_date(r.get("date")),
                "reference":   str(r.get("reference", "") or ""),
                "description": str(r.get("description", "") or ""),
                "amount":      amt,
                "type":        ttype,
            })

        return pd.DataFrame(rows)

    def _to_float(self, val) -> float | None:
        if val is None or str(val).strip() in ("", "nan", "None"):
            return None
        try:
            return float(str(val).replace(",", ".").replace(" ", ""))
        except Exception:
            return None

    def _to_date(self, val):
        if val is None:
            return date.today()
        if hasattr(val, "date"):
            return val.date()
        import dateutil.parser as dp
        try:
            return dp.parse(str(val)).date()
        except Exception:
            return date.today()


# ─── Bank-specific parsers (to be expanded) ──────────────────────────────────
class BanescoParser(GenericExcelParser):
    """Banesco — usa el parser genérico, se puede especializar más adelante."""
    pass

class MercantilParser(GenericExcelParser):
    pass

class ProvincialParser(GenericExcelParser):
    pass

class BNCParser(GenericExcelParser):
    pass

class ExteriorParser(GenericExcelParser):
    pass

class PlazaParser(GenericExcelParser):
    pass

class BancaribeParser(GenericExcelParser):
    pass


# ─── PDF Parsers ─────────────────────────────────────────────────────────────
class BNCPDFParser(BaseParser):
    """Parser nativo para extraer tablas del PDF del Banco Nacional de Crédito."""
    def parse(self, file_path: str) -> pd.DataFrame:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("Es necesario instalar 'pdfplumber' para analizar PDFs.")

        rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                
                for row in table:
                    # Ignore empty rows
                    if not row or not row[0]:
                        continue
                    
                    # Ignore header
                    fecha_str = str(row[0]).strip()
                    if "Fecha" in fecha_str or "Movimientos" in fecha_str:
                        continue
                    
                    # Ensure row has enough columns
                    if len(row) < 8:
                        continue
                        
                    # Validating DD/MM/YYYY roughly
                    if len(fecha_str) != 10 or "/" not in fecha_str:
                        continue
                        
                    referencia = str(row[5]).strip() if row[5] else ""
                    # Merge multi-line text into a single string
                    descripcion = str(row[4]).strip().replace('\n', ' ') if row[4] else ""
                    
                    debe_str = str(row[6]).strip() if row[6] else ""
                    haber_str = str(row[7]).strip() if row[7] else ""
                    
                    debe = self._parse_amount(debe_str)
                    haber = self._parse_amount(haber_str)
                    
                    amount = 0.0
                    ttype = "CARGO"
                    
                    if debe > 0:
                        amount = debe
                        ttype = "CARGO"
                    elif haber > 0:
                        amount = haber
                        ttype = "ABONO"
                    else:
                        continue
                        
                    from datetime import datetime
                    try:
                        date_obj = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                    except ValueError:
                        date_obj = date.today()
                        
                    rows.append({
                        "date": date_obj,
                        "reference": referencia,
                        "description": descripcion,
                        "amount": amount,
                        "type": ttype
                    })
                    
        return pd.DataFrame(rows)

    def _parse_amount(self, val_str: str) -> float:
        if not val_str or val_str in ("0,00", "0.00", "0", ""):
            return 0.0
        val_str = val_str.replace("+", "").replace("-", "").strip()
        val_str = val_str.replace(".", "")
        val_str = val_str.replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return 0.0


# ─── Factory ─────────────────────────────────────────────────────────────────
class ParserFactory:
    _MAP = {
        "banesco":                 BanescoParser,
        "mercantil":               MercantilParser,
        "banco provincial (bbva)": ProvincialParser,
        "banco nacional de crédito (bnc)": BNCParser,
        "banco exterior":          ExteriorParser,
        "banco plaza":             PlazaParser,
        "bancaribe":               BancaribeParser,
        # PDF Mappings
        "banco nacional de crédito (bnc) (pdf)": BNCPDFParser,
    }

    @staticmethod
    def get_parser(bank_name: str, file_path: str = "") -> BaseParser:
        key = bank_name.lower().strip()
        parser_class = ParserFactory._MAP.get(key, GenericExcelParser)
        return parser_class()
