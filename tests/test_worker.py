import subprocess
from unittest.mock import Mock, patch
import pytest
from attgames.pipeline import run_worker


def test_timeout_kills_all_render_processes():
    process = Mock(pid=123)
    process.communicate.side_effect = [subprocess.TimeoutExpired('worker', 1800), ('', '')]
    with patch('attgames.pipeline.subprocess.Popen', return_value=process), patch('attgames.pipeline.os.killpg') as kill:
        with pytest.raises(subprocess.TimeoutExpired): run_worker('job')
    kill.assert_called_once()
    assert kill.call_args.args[0] == 123
    assert process.communicate.call_count == 2
