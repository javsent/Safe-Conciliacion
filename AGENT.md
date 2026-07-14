# Agent Directive & Architecture Reference (`AGENT.md`)

Welcome! This document contains the core axioms, architecture, database schemas, and UX directives for **Safe Conciliación**. Read this first before modifying or adding features.

---

## 🏛️ Architecture & Technologies

1. **Language & GUI Framework**: Python 3.x + PyQt6.
2. **Design System**: [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) (QFluentWidgets). 
   - **Theme Directive**: The application enforces **Theme.LIGHT** globally. Do not introduce dark mode features or override system theme unless requested. 
   - **Dialog Directive**: Standard `QDialog` overlays must set a white background (`background-color: #ffffff;`) to avoid lack of contrast in Windows environment.
3. **Database Layer**: SQLite + SQLAlchemy. DB file is local (`conciliacion.db`).
4. **Data Science Libraries**: `pandas` (for generic tabular data parsers) and `pdfplumber` (for native PDF statement table extraction).

---

## 💾 Core Database Schema Reference

### `Condominium`
- Represents a commercial/residential complex.
- Has many `clients`, `suppliers`, and `transactions`.

### `Client` (Extended for Copropietarios)
- `property_code` (str): Unit identifier (e.g., `16-A`).
- `name` (str): Emitter / owner's full name.
- `cedula_rif` (str): National ID or tax ID.
- `phone` (str): Phone numbers (semicolon separated).
- `email` (str): Primary contact email.
- `keywords` (str): Semicolon-separated tags (e.g., `pago movil; transferencia`) used for matching transactions.
- `account_numbers` (str): Linked bank accounts.

### `Supplier`
- Represents vendors or service providers.

### `Transaction`
- Represents a bank statement record.
- `transaction_type` (Enum): `ABONO` (Deposit/Credit) or `CARGO` (Withdrawal/Debit).
- `status` (Enum): `CONCILIADO`, `SIN_CONCILIAR`, or `OTRO`.
- `status_note` (str): Optional note for the 'OTRO' status.

---

## 🛠️ Key Axioms & Development Directives

### 1. Bank Statement Parsing (`core/parser_factory.py`)
- Every parser class inherits from `BaseParser` and implements `parse(file_path) -> pd.DataFrame`.
- The returned DataFrame must have exactly: `date`, `reference`, `description`, `amount`, `type` ("ABONO" or "CARGO").
- **PDF Extraction Axiom**: Use `pdfplumber` for PDF statements. Ensure to strip out formatting noise, join multiline table cell texts (like descriptions), and clean up Spanish/Venezuelan decimal separators (`.` for thousands, `,` for decimals).

### 2. UI Layout Stability (`ui/views/dashboard.py`)
- The header uses a horizontal layout for the title and date filters. 
- The subtitle height is **fixed** (`setFixedHeight(20)`) to prevent vertical shifting when adding custom calendar pickers (`CalendarPicker`) or modifying text.
- Use `CalendarPicker` for custom dates instead of default Windows QDateEdit widgets to preserve Fluent aesthetics.

### 3. Copropietarios Import (`ui/views/entities_view.py`)
- The import spreadsheet expect 6 positional columns: `[Inmueble, Nombre, Cédula, Teléfonos, Correo, Palabras Clave]`.
- Always generate a user template utilizing `openpyxl` with styled headers and a guide row to help users structure their data.
