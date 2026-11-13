"""Runtime paths shared by source installs and frozen Windows builds."""
import os
import shutil
import sys
from pathlib import Path


def bundle_root() -> Path:
    frozen = getattr(sys, "_MEIPASS", None)
    return Path(frozen).resolve() if frozen else Path(__file__).resolve().parents[1]


def resource(*parts: str) -> Path:
    return bundle_root().joinpath(*parts)


def executable(name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    bundled = resource("bin", name + suffix)
    if bundled.is_file():
        return str(bundled)
    found = shutil.which(name)
    if found:
        return found
    raise FileNotFoundError(f"{name} não encontrado no pacote nem no PATH")


def worker_command(root: Path, job_id: str) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--worker", str(root), job_id]
    return [sys.executable, "-m", "attstudio.worker", str(root), job_id]


def is_frozen_windows() -> bool:
    return bool(getattr(sys,'frozen',False) and os.name=='nt')


def default_data_dir() -> Path:
    configured=os.environ.get('ATT_STUDIO_DIR')
    if configured:
        return Path(configured).expanduser().resolve()
    if is_frozen_windows():
        base=os.environ.get('LOCALAPPDATA')
        if not base:
            raise RuntimeError('LOCALAPPDATA indisponível no Windows')
        return Path(base)/'ATT DOS GAMES Studio'/'data'
    return Path('studio-data').resolve()
