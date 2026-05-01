"""Runtime path helpers for desktop and Android builds."""

import os
from pathlib import Path
from typing import List, Optional


APP_ROOT = Path(__file__).resolve().parent.parent
_selected_root: Optional[Path] = None


def is_android() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ


def asset_path(*parts: str) -> Path:
    return APP_ROOT.joinpath(*parts)


def user_data_dir() -> Path:
    if is_android():
        base = os.environ.get("ANDROID_PRIVATE") or os.environ.get("ANDROID_ARGUMENT")
        if base:
            return Path(base)
    return APP_ROOT


def external_storage_dir() -> Path:
    if is_android():
        try:
            from android.storage import primary_external_storage_path

            return Path(primary_external_storage_path())
        except Exception:
            pass
        for path in ("/storage/emulated/0", "/sdcard"):
            candidate = Path(path)
            if candidate.exists():
                return candidate
    return APP_ROOT


def root_choice_file() -> Path:
    return user_data_dir() / "taikomini_root.txt"


def load_selected_root() -> Optional[Path]:
    global _selected_root
    if _selected_root is not None:
        return _selected_root
    try:
        choice_file = root_choice_file()
        if choice_file.exists():
            value = choice_file.read_text(encoding="utf-8").strip()
            if value:
                _selected_root = Path(value)
                return _selected_root
    except Exception:
        pass
    return None


def set_taikomini_root(path: Path) -> None:
    global _selected_root
    _selected_root = Path(path).expanduser()
    try:
        choice_file = root_choice_file()
        choice_file.parent.mkdir(parents=True, exist_ok=True)
        choice_file.write_text(str(_selected_root), encoding="utf-8")
    except Exception as exc:
        print(f"Failed to save taikomini root: {exc}")


def taikomini_root_candidates() -> List[Path]:
    override = os.environ.get("TAIKOMINI_SONGS_DIR")
    if override:
        override_path = Path(override).expanduser()
        return [override_path.parent if override_path.name.lower() == "songs" else override_path]

    external_root = external_storage_dir()
    selected_root = load_selected_root()
    candidates = (
        *((selected_root,) if selected_root else ()),
        external_root / "taikomini",
        external_root / "TaikoMini",
        external_root / "Download" / "taikomini",
        external_root / "Download" / "TaikoMini",
        user_data_dir() / "taikomini",
        APP_ROOT,
    )

    unique = []
    seen = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def find_taikomini_root() -> Path:
    candidates = taikomini_root_candidates()
    for path in candidates:
        if (path / "songs").exists() and any((path / "songs").glob("**/*.tja")):
            return path
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def taikomini_root() -> Path:
    return find_taikomini_root()


def songs_dir() -> Path:
    return taikomini_root() / "songs"


def resource_dir() -> Path:
    return taikomini_root() / "Resource"


def config_file(name: str = "config.ini") -> Path:
    return taikomini_root() / name
