from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.insert_or_update import upsert_generic
from management.seed.constants import CHILDREN_FIELD, KEY_FIELD
from management.seed.registry import is_join_entity

UUID_NAMESPACE = uuid.UUID("2f0b8a7a-5c6a-4b88-9a1a-0f3d5d7b9e11")


@dataclass(frozen=True)
class SeedRecord:
    model_key: str
    Model: Any
    row: dict[str, Any]


def deterministic_id_from_key(key: str) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, key))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _get_key(row: dict[str, Any]) -> str:
    """
    Контракт: __key__ обязателен.
    Временно поддерживаем _key для обратной совместимости.
    """
    key = row.get(KEY_FIELD)
    if not key:
        raise RuntimeError(f"Отсутствует обязательное поле {KEY_FIELD}: {row}")
    return str(key)


def flatten_payload(payload: dict[str, Any], registry: dict[str, Any]) -> list[SeedRecord]:
    records: list[SeedRecord] = []
    for raw_key, rows in payload.items():
        if not isinstance(raw_key, str):
            raise RuntimeError(f"Ключ верхнего уровня в JSON должен быть строкой, получено: {type(raw_key)}")

        lookup = raw_key.strip().lower()
        if lookup not in registry:
            raise RuntimeError(
                f"Неизвестная модель '{raw_key}' в JSON. "
                "Допустимо: имя класса ORM / __tablename__ / snake_case имени класса."
            )

        if not isinstance(rows, list):
            raise RuntimeError(f"Ожидается список записей для '{raw_key}', получено: {type(rows)}")

        Model = registry[lookup]
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"Ожидается объект(dict) для '{raw_key}', получено: {type(row)}")
            records.append(SeedRecord(raw_key, Model, row))

    return records


def split_scalars_and_children(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """
    Однозначное правило:
    - Вложенные сущности (O2M) описываются ТОЛЬКО через __children__.
    - Любые другие списки (включая list[dict]) — это значения полей.
    """
    scalars = dict(row)
    children: dict[str, list[dict[str, Any]]] = {}

    raw_children = scalars.pop(CHILDREN_FIELD, None)
    if raw_children is None:
        return scalars, children

    if not isinstance(raw_children, dict):
        raise RuntimeError(f"'{CHILDREN_FIELD}' должен быть объектом (dict).")

    for model_key, items in raw_children.items():
        if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
            raise RuntimeError(f"'{CHILDREN_FIELD}.{model_key}' должен быть list[dict].")
        children[model_key] = items

    return scalars, children


def prepare_row(Model: Any, row: dict[str, Any], key_to_id: dict[str, str]) -> dict[str, Any]:
    mapper = sa_inspect(Model)
    columns = {c.key: c for c in mapper.columns}

    seed_key = _get_key(row)

    prepared: dict[str, Any] = {}

    for k, v in row.items():
        if k in (KEY_FIELD, CHILDREN_FIELD):
            continue

        if k not in columns:
            # допускаем лишние поля в JSON
            continue

        col = columns[k]

        # FK: если значение строка и совпадает с __key__ другой сущности
        if col.foreign_keys and isinstance(v, str) and v in key_to_id:
            v = key_to_id[v]

        prepared[k] = v

    # если у модели есть id — обеспечиваем его
    if "id" in columns:
        prepared["id"] = str(row.get("id") or prepared.get("id") or deterministic_id_from_key(seed_key))

    return prepared


async def upsert_by_pk(session: AsyncSession, Model: Any, values: dict[str, Any]) -> None:
    """
    Upsert по PK:
    - PK может быть составным (join table)
    - exclude_on_update = PK поля
    Важно: upsert_generic должен корректно отрабатывать случай, когда update set пустой
    (для чистых join-таблиц нужен ON CONFLICT DO NOTHING).
    """
    mapper = sa_inspect(Model)
    pk_keys = [c.key for c in mapper.primary_key]
    if not pk_keys:
        raise RuntimeError(f"У модели {Model.__name__} не найден primary key")

    index_elements = [getattr(Model, k) for k in pk_keys]
    exclude_on_update = tuple(pk_keys)

    await upsert_generic(
        session=session,
        model=Model,
        values=values,
        index_elements=index_elements,
        exclude_on_update=exclude_on_update,
    )


async def seed_payload(session: AsyncSession, payload: dict[str, Any], registry: dict[str, Any]) -> None:
    records = flatten_payload(payload, registry)

    # __key__ -> id
    key_to_id: dict[str, str] = {}
    for rec in records:
        seed_key = _get_key(rec.row)
        key_to_id[seed_key] = str(rec.row.get("id") or deterministic_id_from_key(seed_key))

    normal = [r for r in records if not is_join_entity(r.Model)]
    join = [r for r in records if is_join_entity(r.Model)]

    # Шаг 1 — сущности + O2M
    for rec in normal:
        scalars, children = split_scalars_and_children(rec.row)

        parent_values = prepare_row(rec.Model, scalars, key_to_id)
        await upsert_by_pk(session, rec.Model, parent_values)

        parent_id = key_to_id[_get_key(rec.row)]
        parent_table = sa_inspect(rec.Model).persist_selectable.name

        for child_key, items in children.items():
            child_lookup = child_key.strip().lower()
            if child_lookup not in registry:
                raise RuntimeError(
                    f"Неизвестная вложенная модель '{child_key}'. "
                    "Допустимо: имя класса ORM / __tablename__ / snake_case."
                )

            ChildModel = registry[child_lookup]
            child_mapper = sa_inspect(ChildModel)

            fk_to_parent: str | None = None
            for col in child_mapper.columns:
                for fk in col.foreign_keys:
                    if fk.column.table.name == parent_table:
                        fk_to_parent = col.key
                        break
                if fk_to_parent:
                    break

            if not fk_to_parent:
                raise RuntimeError(f"Не найден FK у '{ChildModel.__name__}' на '{rec.Model.__name__}'.")

            for child in items:
                child_seed_key = _get_key(child)

                # если у ChildModel есть id — мы его заполним в prepare_row, но для маппинга
                # (если дальше кто-то будет ссылаться на ребёнка) добавим сразу
                key_to_id.setdefault(child_seed_key, child.get("id") or deterministic_id_from_key(child_seed_key))

                # проставляем FK на родителя
                child[fk_to_parent] = parent_id

                child_values = prepare_row(ChildModel, child, key_to_id)
                await upsert_by_pk(session, ChildModel, child_values)

    # Шаг 2 — join-entity (M2M)
    for rec in join:
        values = prepare_row(rec.Model, rec.row, key_to_id)
        await upsert_by_pk(session, rec.Model, values)


async def seed_files(session: AsyncSession, paths: list[Path], registry: dict[str, Any]) -> None:
    for path in paths:
        payload = load_json(path)
        await seed_payload(session, payload, registry)
