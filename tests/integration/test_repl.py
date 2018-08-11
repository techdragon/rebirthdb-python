import pytest
from rebirthdb import RebirthDB


@pytest.mark.integration
def test_repl_does_not_require_connection(function_scoped_rebirthdb_server_with_function_unique_db_connection):
    r = RebirthDB()
    connection = function_scoped_rebirthdb_server_with_function_unique_db_connection
    target_db = function_scoped_rebirthdb_server_with_function_unique_db_connection.db
    connection.repl()
    databases = r.db_list().run()
    assert target_db in databases
