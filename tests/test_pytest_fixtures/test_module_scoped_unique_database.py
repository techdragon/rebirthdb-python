import rebirthdb
import uuid


r = rebirthdb.RebirthDB()


TEST_TABLE_NAME = uuid.uuid4().hex


def test_database_exists(module_scoped_rebirthdb_server_with_module_unique_db_connection):
    target_db = module_scoped_rebirthdb_server_with_module_unique_db_connection.db
    connection = module_scoped_rebirthdb_server_with_module_unique_db_connection
    try:
        r.db_create(target_db).run(connection)
    except rebirthdb.errors.ReqlOpFailedError as desired_error:
        assert desired_error.args[0][:8] == 'Database'
        assert desired_error.args[0][-15:] == 'already exists.'


def test_make_table(module_scoped_rebirthdb_server_with_module_unique_db_connection):
    target_db = module_scoped_rebirthdb_server_with_module_unique_db_connection.db
    connection = module_scoped_rebirthdb_server_with_module_unique_db_connection
    result = r.db(target_db).table_create(TEST_TABLE_NAME).run(connection)
    assert result["tables_created"] == 1


def test_table_still_exists_in_subsequent_test_function(
        module_scoped_rebirthdb_server_with_module_unique_db_connection):

    connection = module_scoped_rebirthdb_server_with_module_unique_db_connection
    result = r.table_list().run(connection)
    assert TEST_TABLE_NAME in result
