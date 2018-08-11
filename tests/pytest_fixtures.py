import socket
import uuid
import logging
import os
import platform

import pytest

from pytest_fixture_config import requires_config
from pytest_fixture_config import Config
from pytest_server_fixtures.base import TestServer


LOG = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
rebirthdb = None


class ReBirthDBFixtureConfig(Config):
    __slots__ = (
        'rebirth_executable',
        'fixture_hostname',
        'remote_server',
        'docker_server',
    )


# TODO: This default doesnt appear to work properly. Decide its fate.
DEFAULT_SERVER_FIXTURES_HOSTNAME = socket.gethostname()

PLATFORM_PATHS = {
    'Darwin': "/usr/local/bin/rethinkdb",
    'Linux': "/usr/bin/rebirthdb",
}
DEFAULT_SERVER_FIXTURES_REBIRTH = PLATFORM_PATHS[platform.system()]


CONFIG = ReBirthDBFixtureConfig(
    fixture_hostname=os.getenv('SERVER_FIXTURES_HOSTNAME', DEFAULT_SERVER_FIXTURES_HOSTNAME),
    rebirth_executable=os.getenv('SERVER_FIXTURES_RETHINK', DEFAULT_SERVER_FIXTURES_REBIRTH),
    remote_server=False,
    docker_server=False,
)


class ReBirthDBServer(TestServer):
    random_port = True
    connection = None

    def __init__(self, **kwargs):
        global rebirthdb
        try:
            # noinspection PyUnresolvedReferences
            from rebirthdb import RebirthDB
            rebirthdb = RebirthDB()
        except ImportError:
            pytest.skip('rebirthdb not installed, skipping test')
        super(ReBirthDBServer, self).__init__(**kwargs)
        self.cluster_port = self.get_port()
        self.http_port = self.get_port()
        self.db = None

    @property
    def run_cmd(self):
        run_command = [
            CONFIG.rebirth_executable,
            '--directory', self.workspace / 'db',
            '--driver-port', str(self.port),
            '--http-port', str(self.http_port),
            '--cluster-port', str(self.cluster_port),
            '--bind', socket.gethostbyname(self.hostname),
        ]
        return run_command

    def check_server_up(self):
        """Test connection to the server."""
        LOG.info("Connecting to ReBirthDB at {0}:{1}".format(self.hostname, self.port))
        try:
            self.connection = rebirthdb.connect(host=self.hostname, port=self.port, db='test')
            return True
        except rebirthdb.RqlDriverError as err:
            LOG.warning(err)
        return False


def _rebirthdb_server(request):
    """ Generic, reusable RebirthDB setup/startup function.
    """
    # test_server = ReBirthDBServer(hostname=CONFIG.fixture_hostname, random_port=CONFIG.random_port)
    test_server = ReBirthDBServer(hostname=CONFIG.fixture_hostname)
    request.addfinalizer(lambda p=test_server: p.teardown())
    test_server.start()
    return test_server


@requires_config(CONFIG, ['rebirth_executable'])
@pytest.fixture(scope='function')
def rebirthdb_server_function_scoped(request):
    """ Function scoped ReBirthDB server. """
    return _rebirthdb_server(request)


@requires_config(CONFIG, ['rebirth_executable'])
@pytest.fixture(scope='module')
def rebirthdb_server_module_scoped(request):
    """ Module scoped RebirthDB fixture. """
    return _rebirthdb_server(request)


@requires_config(CONFIG, ['rebirth_executable'])
@pytest.fixture(scope='session')
def rebirthdb_server_session_scoped(request):
    """ Session scoped RebirthDB fixture.

        This produces a server that is shared by all tests directly using it and any fixtures built from it.
        Use with care as being shared can result in data leakage problems or other side effects between tests.
    """
    return _rebirthdb_server(request)


# noinspection PyShadowingNames
@pytest.yield_fixture(scope="function")
def function_scoped_rebirthdb_server_with_function_unique_db_connection(rebirthdb_server_function_scoped):
    """ A function scoped server that returns a unique database for each function using this fixture.

        This uses a module scoped server, and returns a connection to a unique database to each test function
        that uses this fixture, and drops the database after the test function completes.
    """
    dbid = uuid.uuid4().hex
    connection = rebirthdb_server_function_scoped.connection
    LOG.info("Making database")
    rebirthdb.db_create(dbid).run(connection)
    connection.use(dbid)
    yield connection
    LOG.info("Dropping database")
    rebirthdb.db_drop(dbid).run(connection)


# noinspection PyShadowingNames
@pytest.yield_fixture(scope="function")
def module_scoped_rebirthdb_server_with_function_unique_db_connection(rebirthdb_server_module_scoped):
    """ A module scoped server that returns a unique database for each function using this fixture.

        This uses a module scoped server, and returns a connection to a unique database to each test function
        that uses this fixture, and drops the database after the test function completes.
    """
    dbid = uuid.uuid4().hex
    connection = rebirthdb_server_module_scoped.connection
    LOG.info("Making database")
    rebirthdb.db_create(dbid).run(connection)
    connection.use(dbid)
    yield connection
    LOG.info("Dropping database")
    rebirthdb.db_drop(dbid).run(connection)


# noinspection PyShadowingNames
@pytest.yield_fixture(scope="module")
def module_scoped_rebirthdb_server_with_module_unique_db_connection(rebirthdb_server_module_scoped):
    """ Return a module unique server and a module unique database.

        Starts up a module scoped server, returning a connection to a unique database for all the tests in a module.
        We drop the database after module tests are complete.
    """
    dbid = uuid.uuid4().hex
    connection = rebirthdb_server_module_scoped.connection
    LOG.info("Making database")
    rebirthdb.db_create(dbid).run(connection)
    connection.use(dbid)
    yield connection
    LOG.info("Dropping database")
    rebirthdb.db_drop(dbid).run(connection)


# noinspection PyShadowingNames
@pytest.fixture(scope="module")
def make_tables(request, module_scoped_rebirthdb_server_with_module_unique_db_connection):
    """ Module scoped fixture to create tables specified by the module level variable named FIXTURE_TABLES. """
    fixture_table_list = getattr(request.module, 'FIXTURE_TABLES')
    LOG.debug("Do stuff before all module tests with {0}".format(fixture_table_list))
    connection = module_scoped_rebirthdb_server_with_module_unique_db_connection
    LOG.debug(str(fixture_table_list))

    for table_name, primary_key in fixture_table_list:
        try:
            rebirthdb.db(connection.db).table_create(table_name, primary_key=primary_key).run(connection)
            LOG.info('Made table "{0}" with key "{1}"'.format(table_name, primary_key))
        except rebirthdb.errors.RqlRuntimeError as err:
            LOG.debug('Table "{0}" not made: {1}'.format(table_name, err.message))


# noinspection PyShadowingNames,PyUnusedLocal
@pytest.yield_fixture(scope="function")
def rebirth_empty_db(request, module_scoped_rebirthdb_server_with_module_unique_db_connection, make_tables):
    """ Function scoped fixture that empties the tables defined for use by the `make_tables` fixture.

        This will sometimes be useful because of the time it takes to create a new ReBirthDB table,
        compared to the time it takes to empty one.
    """
    tables_to_emptied = (table[0] for table in getattr(request.module, 'FIXTURE_TABLES'))
    connection = module_scoped_rebirthdb_server_with_module_unique_db_connection

    for table_name in tables_to_emptied:
        rebirthdb.db(connection.db).table(table_name).delete().run(connection)
        LOG.debug('Emptied "{0}" before test'.format(table_name))

    yield connection
