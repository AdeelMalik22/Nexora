from django.db import migrations


TABLES = (
    "tenants_branch",
    "tenants_shopmodule",
    "accounts_role",
    "accounts_shopmembership",
    "accounts_device",
    "audit_auditlog",
)


def enable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in TABLES:
            policy = f"{table.replace('_', '')}_tenant_policy"
            cursor.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            cursor.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
            cursor.execute(
                f"CREATE POLICY {policy} ON {table} USING "
                "(shop_id = NULLIF(current_setting('nexora.shop_id', true), '')::uuid)"
            )


def disable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in TABLES:
            policy = f"{table.replace('_', '')}_tenant_policy"
            cursor.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
            cursor.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


class Migration(migrations.Migration):
    dependencies = [("tenants", "0001_initial"), ("accounts", "0001_initial"), ("audit", "0001_initial")]
    operations = [migrations.RunPython(enable_rls, disable_rls)]
