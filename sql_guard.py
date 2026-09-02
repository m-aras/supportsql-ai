import sqlglot
from sqlglot import exp

DANGEROUS_FUNCTIONS = {
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_stat_file",
    "lo_import",
    "lo_export",
    "dblink",
    "dblink_connect",
    "pg_sleep",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_reload_conf",
}

DATA_MODIFYING_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
)

def validate_sql(sql: str):
    if not sql or not sql.strip():
        return False, "Boş SQL sorgusu."

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as e:
        return False, f"SQL parse edilemedi: {e}"

    statements = [s for s in statements if s is not None]

    if len(statements) == 0:
        return False, "Geçerli bir SQL statement'ı bulunamadı."

    if len(statements) != 1:
        return False, "Sadece tek bir sorguya izin veriliyor (birden fazla statement tespit edildi)."

    stmt = statements[0]

    if stmt.key != "select":
        return False, f"Sadece SELECT sorgularına izin veriliyor (tespit edilen komut tipi: {stmt.key})."

    
    for node in stmt.walk():
        n = node[0] if isinstance(node, tuple) else node
        if isinstance(n, DATA_MODIFYING_NODE_TYPES):
            return False, "Sorgu içinde izin verilmeyen bir veri değiştirme işlemi tespit edildi."

   
    for func in stmt.find_all(exp.Anonymous):
        if func.name and func.name.lower() in DANGEROUS_FUNCTIONS:
            return False, f"İzin verilmeyen fonksiyon çağrısı: {func.name}"

    return True, ""