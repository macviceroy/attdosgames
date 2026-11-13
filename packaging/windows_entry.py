from multiprocessing import freeze_support
import os
from pathlib import Path
import sys
import tempfile
import traceback

if __name__=='__main__':
    freeze_support()
    # Windowed Python has no standard streams. Uvicorn and dependencies still
    # expect writable streams; preserve diagnostics without a modal error box.
    log_path=Path(os.environ.get('ATT_STUDIO_LOG', str(Path(tempfile.gettempdir())/'att-studio.log')))
    if sys.stdout is None or sys.stderr is None:
        log_path.parent.mkdir(parents=True,exist_ok=True)
        log=log_path.open('a',encoding='utf-8',buffering=1)
        if sys.stdout is None:sys.stdout=log
        if sys.stderr is None:sys.stderr=log
    try:
        from attstudio.__main__ import main
        main()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
