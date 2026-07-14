# Changelog

All notable changes to the **Safe Conciliación** project will be documented in this file.

---

## [1.2.0] - 2026-07-14

### Added
- **Copropietarios Import Support**:
  - Updated SQLite database schema and SQLAlchemy models for `Client` to include `property_code`, `email`, and `keywords`.
  - Added "Descargar Plantilla" button to export a styled `.xlsx` template for owners' registration.
  - Added "Importar desde archivo" button to bulk load owners from `.xlsx` or `.csv` files.
- **BNC PDF Parser**:
  - Integrated `pdfplumber` to extract native bank statement tables from BNC checkings PDFs.
  - Built robust sanitization for currency formats (e.g., `-55.442,58` to Float).
- **Tabbed Import Interface**:
  - Separated "Excel / CSV" and "PDF" imports inside `ImportDialog` using a `SegmentedWidget`.

### Changed
- **Global Theme & Contrast Adjustments**:
  - Forced `Theme.LIGHT` globally via PyQt-Fluent-Widgets configuration.
  - Resolved low-contrast issues in modal overlays (e.g., add condominium, import dialogs) by overriding default `QDialog` background colors to white.

---

## [1.1.0] - 2026-06-08

### Added
- **Dashboard Date Filters**:
  - Implemented quick date range filters ("Este Mes", "Mes Pasado", "Histórico Completo").
  - Integrated QFluentWidgets `CalendarPicker` widgets to allow custom date range selection dynamically.

### Changed
- **UX Alignment Fixes**:
  - Replaced combo boxes for active condominium selection with a `NavigationAvatarWidget` inside the sidebar.
  - Moved the search bar in the conciliation tab to the top right header for better visibility.
  - Removed mixed unicode emoji symbols from transaction status buttons to solve text misalignment on Windows.

---

## [1.0.0] - 2026-06-02

### Added
- Initial project structure.
- SQLite connection layer with SQLAlchemy models (`Condominium`, `Client`, `Supplier`, `Transaction`).
- Parser factory setup supporting XLS/CSV/TXT bank statements.
- CRUD logic and core application UI.
