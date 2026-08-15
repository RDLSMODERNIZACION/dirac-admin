# Central whitelist. This prevents arbitrary table access through the generic CRUD router.
# generated/read-only fields are intentionally omitted from writable fields.

TABLES: dict[str, dict] = {
    "clients": {
        "writable": ["name", "tax_id", "contact_name", "email", "phone", "address", "notes", "is_active"],
        "search": ["name", "tax_id", "contact_name", "email"],
    },
    "works": {
        "writable": ["code", "client_id", "name", "description", "type", "status", "start_date", "end_date", "contract_amount", "monthly_amount", "billing_frequency", "billing_day", "estimated_cost", "progress_percent", "notes"],
        "search": ["code", "name", "description", "type", "status"],
    },
    "work_progress": {
        "writable": ["work_id", "progress_date", "physical_progress_percent", "description", "notes", "created_by"],
        "search": ["description", "notes"],
    },
    "work_items": {
        "writable": ["work_id", "code", "description", "unit", "quantity", "unit_price", "weight_percent", "progress_percent", "status", "notes"],
        "search": ["code", "description", "unit", "status", "notes"],
    },
    "work_budget_items": {
        "writable": ["work_id", "category", "description", "budget_amount", "notes"],
        "search": ["category", "description", "notes"],
    },
    "work_costs": {
        "writable": ["work_id", "supplier_id", "cost_date", "category", "concept", "quantity", "unit", "unit_price", "payment_status", "due_date", "paid_at", "invoice_number", "payable_id", "notes"],
        "search": ["category", "concept", "unit", "payment_status", "invoice_number", "notes"],
    },
    "work_certificates": {
        "writable": ["work_id", "certificate_number", "period_from", "period_to", "progress_percent", "gross_amount", "retention_amount", "status", "notes"],
        "search": ["certificate_number", "status", "notes"],
    },
    "work_documents": {
        "writable": ["work_id", "document_type", "title", "description", "file_name", "file_path", "mime_type", "file_size", "related_type", "related_id", "document_date"],
        "search": ["document_type", "title", "description", "file_name", "related_type"],
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
        "writable": ["client_id", "work_id", "description", "document_number", "issue_date", "due_date", "amount", "status", "notes", "document_id"],
        "search": ["description", "document_number", "status", "notes"],
    },
    "payables": {
        "writable": ["supplier_id", "work_id", "purchase_id", "supplier_service_id", "description", "document_number", "issue_date", "due_date", "amount", "category", "status", "notes", "document_id"],
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
