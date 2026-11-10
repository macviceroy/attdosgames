from unittest.mock import patch
import pytest
from attgames.pipeline import produce, store


def test_retry_only_failed_and_limited(tmp_path, monkeypatch):
    monkeypatch.setenv('ATT_DATA_DIR', str(tmp_path))
    with patch('attgames.pipeline.run_worker', side_effect=RuntimeError('offline')) as worker:
        first = produce('Teste')
        duplicate = produce('Teste')
        assert worker.call_count == 1
        assert first['id'] == duplicate['id']
        second = produce('Teste', retry=True)
        assert second['attempts'] == 2
        third = produce('Teste', retry=True)
        assert third['attempts'] == 3
        with pytest.raises(ValueError, match='Limite'): produce('Teste', retry=True)
    assert len(store().events(first['id'])) >= 6
