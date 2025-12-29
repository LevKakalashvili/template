import asyncio
import os
from pathlib import Path

from db.database_async import session_scope
from management.base.command import BaseCommand
from management.seed import collect_models_registry, resolve_seed_files, seed_files
from management.seed.logging import setup_cli_logger
from management.seed.manifest import DEFAULT_JSON_GLOB, DEFAULT_MANIFEST_NAME

DEFAULT_RESOURCES_DIR = Path(__file__).resolve().parents[1] / "resources"


def _apply_db_override(db_dsn: str | None) -> None:
    from db import database_async

    final_dsn = db_dsn or os.getenv("POSTGRES_DSN") or database_async.ASYNC_DSN
    if not final_dsn:
        raise RuntimeError(
            "Не удалось определить DSN подключения (нет --db-dsn, POSTGRES_DSN и config.postgres.async_dsn)."
        )

    database_async.ASYNC_DSN = final_dsn
    database_async.init_async_engine()  # type: ignore[attr-defined]


async def _run(
    resources_dir: Path,
    manifest_path: Path,
    files_override: list[str] | None,
    use_all: bool,
    glob_mask: str | None,
    exclude: list[str] | None,
) -> None:
    command_name = Path(__file__).stem  # init_project_templates
    logger = setup_cli_logger(f"management.command.{command_name}")

    paths = resolve_seed_files(
        command_name=command_name,
        resources_dir=resources_dir,
        manifest_path=manifest_path,
        files_override=files_override,
        use_all=use_all,
        glob_mask=glob_mask,
        exclude=exclude,
    )

    logger.info(f"Seed files for '{command_name}': {', '.join(str(p) for p in paths)}")

    registry = collect_models_registry()

    async with session_scope() as session:
        await seed_files(session, paths, registry)

    logger.info("Init completed.")


class Command(BaseCommand):
    help = "Init project templates from JSON"

    def add_arguments(self):
        self.parser.add_argument("--resources-dir", default=str(DEFAULT_RESOURCES_DIR))
        self.parser.add_argument("--manifest", default=str(DEFAULT_RESOURCES_DIR / DEFAULT_MANIFEST_NAME))

        self.parser.add_argument("--files", nargs="*", default=None, help="Явно указать список json файлов")
        self.parser.add_argument("--all", action="store_true", help="Загрузить все json из папки resources")

        self.parser.add_argument("--file-glob", default=DEFAULT_JSON_GLOB)
        self.parser.add_argument("--exclude", nargs="*", default=None)

        self.parser.add_argument("--db-dsn", dest="db_dsn", required=False, default=None)

    def execute(self):
        _apply_db_override(self.args.db_dsn)
        asyncio.run(
            _run(
                resources_dir=Path(self.args.resources_dir),
                manifest_path=Path(self.args.manifest),
                files_override=self.args.files,
                use_all=bool(self.args.all),
                glob_mask=str(self.args.file_glob) if self.args.file_glob else None,
                exclude=self.args.exclude,
            )
        )
