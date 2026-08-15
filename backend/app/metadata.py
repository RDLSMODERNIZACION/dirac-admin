# Central whitelist. This prevents arbitrary table access through the generic CRUD router.
# generated/read-only fields are intentionally omitted from writable fields.

TABLES: dict[str, dict] = {
    "clients": {
        "writable": ["name", "tax_id", "contact_name", "email", "phone", "address", "notes", "is_active"],
        "search": ["name", "tax_id", "contact_name", "email"],
    },
    "works": {
        "writable": ["code", "client_id", "name", "description", "type", "status", "start_date", "end_date", "contract_amount", "estimated_cost", "progress_percent", "notes"],
        "search": ["code", "name", "description", "type", "status"],
    },
    "work_progress": {
        "writable": ["work_id", "progress_date", "physical_progress_percent", "description", "notes", "created_by"],
        "search": ["description", "notes"],
    },
    "suppliers": {
        "writable": ["name", "tax_id", "type", "contact_name", "email", "phone", "address", "notes", "is_active"],
        "search": ["name", "tax_id", "contact_name", "email", "type"],
    },
    "supplier_rates": {
        "writable": ["supplier_id", "concept", "unit", "unit_price", "valid_from", "valid_to", "is_active"],
        "search": ["concept", "unit"],
    },
    "supplier_services": {
        "writable": ["supplier_id", "work_id", "service_date", "concept", "quantity", "unit", "unit_price", "status", "notes", "approved_by", "approved_at"],
        "search": ["concept", "unit", "status", "notes"],
    },
    "materials": {
        "writable": ["code", "name", "description", "category", "unit", "minimum_stock", "current_cost", "is_active"],
        "search": ["code", "name", "description", "category", "unit"],
    },
    "purchases": {
        "writable": ["supplier_id", "work_id", "purchase_number", "purchase_date", "due_date", "status", "subtotal", "tax_amount", "notes"],
        "search": ["purchase_number", "status", "notes"],
    },
    "purchase_items": {
        "writable": ["purchase_id", "material_id", "description", "quantity", "unit", "unit_price"],
        "search": ["description", "unit"],
    },
    "stock_movements": {
        "writable": ["material_id", "work_id", "supplier_id", "purchase_id", "movement_type", "quantity", "unit_cost", "movement_date", "reference", "notes"],
        "search": ["movement_type", "reference", "notes"],
    },
    "accounts": {
        "writable": ["name", "type", "currency", "initial_balance", "is_active"],
        "search": ["name", "type", "currency"],
    },
    "receivables": {
        "writable": ["client_id", "work_id", "description", "document_number", "issue_date", "due_date", "amount", "status", "notes"],
        "search": ["description", "document_number", "status", "notes"],
    },
    "payables": {
        "writable": ["supplier_id", "work_id", "purchase_id", "supplier_service_id", "description", "document_number", "issue_date", "due_date", "amount", "category", "status", "notes"],
        "search": ["description", "document_number", "category", "status", "notes"],
    },
    "financial_movements": {
        "writable": ["account_id", "work_id", "client_id", "supplier_id", "receivable_id", "payable_id", "type", "category", "description", "amount", "movement_date", "notes"],
        "search": ["type", "category", "description", "notes"],
    },
    "fixed_costs": {
        "writable": ["name", "category", "amount", "frequency", "due_day", "supplier_id", "is_active", "notes"],
        "search": ["name", "category", "frequency", "notes"],
    },
}
