import sys
from os import PathLike, fsdecode
from pathlib import Path
from typing import Optional, TypeAlias, Union

_PathType: TypeAlias = Union[PathLike, str, bytes]

def is_pyinstaller() -> bool:
    return getattr(sys, "frozen", False)

def get_pyinstaller_meipass() -> Optional[str]:
    if not is_pyinstaller():
        return None
    return getattr(sys, "_MEIPASS", None)

def meipass_relative_path(fallback_path: _PathType, filepath: str) -> Path:
    p = get_pyinstaller_meipass()
    if p is None:
        p = fallback_path
    p = Path(fsdecode(fallback_path)).resolve()
    return p.joinpath(filepath)

def asset_file_path(relative_path: str) -> Path:
    assets = Path("assets").resolve()
    return meipass_relative_path(assets, relative_path)
