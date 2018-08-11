import rebirthdb


r = rebirthdb.RebirthDB()


def test_rebirth_server(rebirthdb_server_function_scoped):
    assert rebirthdb_server_function_scoped.check_server_up()
    assert rebirthdb_server_function_scoped.connection.db == 'test'


def test_function_unique_database(module_scoped_rebirthdb_server_with_function_unique_db_connection):
    target_db = module_scoped_rebirthdb_server_with_function_unique_db_connection.db
    connection = module_scoped_rebirthdb_server_with_function_unique_db_connection
    try:
        r.db_create(target_db).run(connection)
    except rebirthdb.errors.ReqlOpFailedError as desired_error:
        assert desired_error.args[0][:8] == 'Database'
        assert desired_error.args[0][-15:] == 'already exists.'
