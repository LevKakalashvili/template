from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST_NAME = "seed_manifest.json"
DEFAULT_JSON_GLOB = "*.json"


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Manifest не найден: {path}")
    data = json.loads(path.read_text("utf-8"))
    if not isinstance(data, dict) or "commands" not in data:
        raise RuntimeError(f"Некорректный manifest: {path}. Ожидаю объект с ключом 'commands'.")
    if not isinstance(data["commands"], dict):
        raise RuntimeError(f"Некорректный manifest: {path}. 'commands' должен быть object.")
    return data


def resolve_seed_files(
    *,
    command_name: str,
    resources_dir: Path,
    manifest_path: Path,
    files_override: list[str] | None,
    use_all: bool,
    glob_mask: str | None,
    exclude: list[str] | None,
) -> list[Path]:
    """
    Приоритеты:
    1) --files file1 file2 ...
    2) --all (glob/exclude берём из manifest.commands.all, если exclude/glob не заданы в CLI)
    3) manifest.commands[command_name].files
    4) manifest.commands["all"].glob/exclude
    5) fallback: *.json
    """
    if not resources_dir.exists():
        raise RuntimeError(f"Директория ресурсов не найдена: {resources_dir}")

    if files_override:
        paths = [resources_dir / f for f in files_override]
        missing = [p for p in paths if not p.exists()]
        if missing:
            raise RuntimeError(f"Файлы из --files не найдены: {', '.join(str(p) for p in missing)}")
        return paths

    manifest = load_manifest(manifest_path)
    commands = manifest["commands"]

    all_cfg = commands.get("all", {}) if isinstance(commands.get("all"), dict) else {}
    all_glob = all_cfg.get("glob", DEFAULT_JSON_GLOB)
    all_exclude = all_cfg.get("exclude", []) if isinstance(all_cfg.get("exclude", []), list) else []

    if use_all:
        eff_glob = glob_mask or all_glob
        eff_exclude = exclude if exclude is not None else all_exclude
        files = sorted(resources_dir.glob(eff_glob))
        files = [p for p in files if p.name not in set(eff_exclude)]
        if not files:
            raise RuntimeError(f"Не найдено файлов по glob='{eff_glob}' в {resources_dir}")
        return files

    cmd_cfg = commands.get(command_name)
    if isinstance(cmd_cfg, dict) and isinstance(cmd_cfg.get("files"), list) and cmd_cfg["files"]:
        paths = [resources_dir / f for f in cmd_cfg["files"]]
        missing = [p for p in paths if not p.exists()]
        if missing:
            raise RuntimeError(
                f"Файлы из manifest для команды '{command_name}' не найдены: {', '.join(str(p) for p in missing)}"
            )
        return paths

    eff_glob = all_glob if not glob_mask else glob_mask
    files = sorted(resources_dir.glob(eff_glob))
    files = [p for p in files if p.name not in set(all_exclude)]
    if files:
        return files

    files = sorted(resources_dir.glob(glob_mask or DEFAULT_JSON_GLOB))
    if not files:
        raise RuntimeError(f"JSON файлы не найдены в {resources_dir} по маске {glob_mask}")
    return files
