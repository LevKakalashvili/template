from __future__ import annotations

from typing import Any


def _snake(name: str) -> str:
    """
    Преобразует CamelCase → snake_case.

    Нужно для того, чтобы JSON мог использовать:
    - имя ORM-класса
    - __tablename__
    - snake_case имя класса
    """
    out: list[str] = []
    for ch in name:
        if ch.isupper() and out:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def collect_models_registry() -> dict[str, Any]:
    """
    Собирает реестр ORM-моделей для разрешения ключей JSON.

    JSON ключ верхнего уровня может быть:
    - именем ORM класса (ProjectTemplates)
    - __tablename__ (project_templates)
    - snake_case имени класса (project_templates)

    Все ключи нормализуются в lower().
    """
    from db import models as models_module

    Base = models_module.Base
    registry: dict[str, Any] = {}

    def add(key: str, model: Any) -> None:
        if not key:
            return
        norm = key.strip().lower()

        # Коллизии считаем ошибкой конфигурации
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
