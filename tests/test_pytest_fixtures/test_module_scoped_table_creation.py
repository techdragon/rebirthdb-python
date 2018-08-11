import rebirthdb

r = rebirthdb.RebirthDB()


FIXTURE_TABLES = [('table_one', 'primary_key_one'), ('table_two', 'primary_key_two')]


def test_make_tables_on_module_scoped_rebirth_server(
        module_scoped_rebirthdb_server_with_module_unique_db_connection, make_tables):

    connection = module_scoped_rebirthdb_server_with_module_unique_db_connection
    target_db = module_scoped_rebirthdb_server_with_module_unique_db_connection.db
    assert r.db(target_db).table_list().run(connection) == ['table_one', 'table_two']
