import importlib
import os

from fastapi import APIRouter

# Создаем корневой роутер
routers = APIRouter()

# Определяем путь, где будут лежать все модули с роутерами
router_modules = [
    module
    for module in os.listdir(os.path.dirname(__file__))
    if module.endswith("_router.py") and module != "__init__.py"
]

# Импортируем каждый модуль динамически и добавляем его роутер
for module in router_modules:
    module_name = module[:-3]  # Убираем расширение '.py'
    router = importlib.import_module(f".{module_name}", package=__name__).router
    routers.include_router(router)
