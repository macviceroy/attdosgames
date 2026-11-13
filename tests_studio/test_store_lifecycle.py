import sqlite3

import pytest

from attstudio.store import Store


def test_connection_closes_after_commit_and_rollback(tmp_path):
    store=Store(tmp_path/'data')
    with store.db() as committed:
        committed.execute("INSERT INTO events(id,message) VALUES('job','saved')")
    with pytest.raises(sqlite3.ProgrammingError,match='closed'):
        committed.execute('SELECT 1')
    with pytest.raises(RuntimeError,match='abort'):
        with store.db() as rolled_back:
            rolled_back.execute("INSERT INTO events(id,message) VALUES('job','discarded')")
            raise RuntimeError('abort')
    with pytest.raises(sqlite3.ProgrammingError,match='closed'):
        rolled_back.execute('SELECT 1')
    assert [event['message'] for event in store.events('job')]==['saved']
