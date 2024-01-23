# Classic Container

Библиотека представляет реализацию IoC контейнера.
## Введение

Библиотека призвана ускорить работу над приложением упрощая запуск приложения и 
разрешение зависимостей.

При отсутствии множественной реализации интерфейсов ручное разрешение 
зависимостей крайне монотонное и однообразное действие. 

Пример простого приложения:
```python
from abc import ABC

# Интерфейс репозитория
class Interface(ABC):
    pass


# Реализация репозитория
class SomeRepository(Interface):
    pass


# Код приложения 
class SomeService:
    
    def __init__(self, repository: Interface):
        self.repository = repository
    
 
# Контроллер   
class SomeController:
    
    def __init__(self, service: SomeService):
        self.service = service

```

Композит для этого приложения при явном описании 


