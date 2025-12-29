from __future__ import annotations

from typing import Any

from sqlalchemy import inspect as sa_inspect


def _snake(name: str) -> str:
    out: list[str] = []
    for ch in name:
        if ch.isupper() and out:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def collect_models_registry() -> dict[str, Any]:
    """
    Разрешаем ключ верхнего уровня как:
      - имя ORM класса
      - __tablename__
      - snake_case имени класса
    Ключи нормализуем lower().
    При коллизиях — падаем.
    """
    from db import models as models_module

    Base = models_module.Base
    registry: dict[str, Any] = {}

    def add(key: str, model: Any) -> None:
        if not key:
            return
        norm = key.strip().lower()
        if norm in registry and registry[norm] is not model:
            existing = registry[norm]
            raise RuntimeError(
                "Коллизия ключей моделей для JSON:\n"
                f"Ключ: '{key}' (нормализован: '{norm}')\n"
                f"Уже связан с: {existing.__module__}.{existing.__name__} "
                f"(таблица: {getattr(existing, '__tablename__', None)})\n"
                f"Пытаемся связать с: {model.__module__}.{model.__name__} "
                f"(таблица: {getattr(model, '__tablename__', None)})\n"
            )
        registry[norm] = model

    for mapper in Base.registry.mappers:
        cls = mapper.class_
        add(cls.__name__, cls)
        add(getattr(cls, "__tablename__", ""), cls)
        add(_snake(cls.__name__), cls)

    return registry


def is_join_entity(Model: Any) -> bool:
    """Join-entity = таблица с >= 2 FK колонками."""
    mapper = sa_inspect(Model)
    fk_cols = [c for c in mapper.columns if c.foreign_keys]
    return len(fk_cols) >= 2
