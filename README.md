# Classic Container

Библиотека представляет реализацию IoC контейнера.

Оглавление:

- [Введение](#Введение)
- [Container](#Container)
  - [register](#register)
  - [add_settings](#add_settings)
  - [reset](#reset)
  - [resolve](#resolve)
- [Settings](#Settings)
  - [init](#init)
  - [factory](#factory)
  - [scope](#scope)
  - [instance](#instance)
## Введение

При написании приложение со слабосвязанной архитектурой, 
приятным, но необязательным элементом является DI контейнер

Данная библиотека реализует контейнер для библиотек семейства пакетов classic. 
Она призвана ускорить работу над приложением упрощая запуск приложения и
разрешение зависимостей.

Для понимания зачем это нужен DI и в каких случаях он применим, 
рекомендуется к прочтению книга:

"Внедрение зависимостей на платформе .NET" Авторы: Вильчинский Н., Симан Марк


Пример простого приложения:

```python
from abc import ABC, abstractmethod


class InterfaceRepo(ABC):

    @abstractmethod
    def get_by_id(self): ...


class Accounts(InterfaceRepo):

    def get_by_id(self):
        print('Обращение к хранилищу данных')


class Account:

    # Dependency Injection
    def __init__(self, repo: InterfaceRepo):
        self.repo = repo


# Ручное разрешение зависимостей 
impl = Accounts()
service = Account(repo=impl)

# Разрешение зависимостей через контейнер
from classic.container import container

container.register(Accounts, Account)
container.build(Account)
```
При малых объемах кода ручное внедрение зависимостей выглядит достаточно 
лаконично. Сборка же через контейнер на оборот, выглядит громоздко. 
При увеличении объемов кода, разница будет в пользу контейнера. 

### Поиск ошибок
При возникновении ошибки бывает сложно понять, что в контейнере пошло не так.

Во время разработки рекомендуется устанавливать пакет в `debug` варианте:
`pip install classic-container[debug]`

Это подтянет пакет `traceback_with_variables`:
https://pypi.org/project/traceback-with-variables/

Для использования вовремя отладки нужно импортировать в композите с ошибкой.

Пример:
```python
from traceback_with_variables import activate_by_import
```
Пример трейса: 
```python
 File "home/classic/container/builder.py", line 105, in build
    instance = factory(**factory_kwargs)
      self = <classic.container.builder.Builder object at 0x7fb37c9a68f0>
      target = <class '__main__.Interface'>
      cached = None
      target_settings = <container.Settings(scope=SINGLETON)>
      target_settings_layer = <classic.container.builder.Builder object at 0x7fb37c9a68f0>
      factory = <class '__main__.ErrorImplementation'>
      factory_settings = <container.Settings(scope=SINGLETON, init={'some_str': [1, 2, 3]})>
      factory_kwargs = {'some_str': [1, 2, 3]}
      signature = <Signature (some_str: str)>
      parameter = <Parameter "some_str: str">
```
В трейслоге вас интересует:
 - `target` запрошенный класс  
 - `target_settings` настройки запрошенного класса 
 - `factory` фабрика построения класса
 - `factory_settings` настройки фабрики
 - `factory_kwargs` подаваемые параметры фабрики
 - `signature` сигнатура фабрики https://docs.python.org/3/library/inspect.html#introspecting-callables-with-the-signature-object
 - `parameter` последний параметр опрошенный в цикле, для которого был вызван `build`

## Container

Предоставляет четыре метода - [`register`](#register), [`add_settings`](#add_settings), [`reset`](#reset) и [`resolve`](#resolve).

- [`register`](#register) нужен для регистрации классов, интерфейсов, функций и даже модулей.

- [`add_settings`](#add_settings) добавляет или обновляет настройки контейнера. 
Ключом является класс, значение - настройки.

- [`reset`](#reset) удаляет добавленные настройки контейнера и ссылки на инстансы уже 
созданных классов

- [`resolve`](#resolve) принимает какой-либо класс (интерфейс), и возвращает инстанс
указанного интерфейс с разрешенными зависимостями.

Ради удобства был сделан дефолтный контейнер, чтобы не инстанцировать каждый 
раз в ручную. Конечно, вы можете создавать свои инстансы контейнера, 
когда вам нужно.

```python
# Импортирование дефолтного контейнера
from classic.container import container

# Самостоятельное создание контейнера
from classic.container import Container

manual_container = Container()
```

В примере выше модуль `container` предоставляет возможность использовать 
методы класса `Container`.

Дальше по каждому методу подробней:

### register
При обращении принимает список компонентов. Определяет тип, заносит в реестр, 
каждому типу сопоставляет список фабрик, способных построить указанный тип.

Существует только один способ зарегистрировать компоненты:
```python
import os
from classic.container import container

def some_factory() -> SomeClass:
    pass

container.register(os, some_factory, Composition)
```

Элементами списка могут быть: абстрактные классы, классы,
фабрики (функции, возвращающие один инстанс любого класса) и модули.

- Абстрактные классы регистрируется в реестре только как ключи, без фабрик.
- Нормальные классы регистрируются как ключ и соответсвующая ему
  фабрика - конструктор самого класса.
- Фабрики регистрируются сложнее, ключом будет являться результат из
  аннотации функции, а значением сама фабрика. Пример:
```python
def some_factory() -> SomeClass:
    # будет зарегистрировано как SomeClass: [some_factory]
    pass
```

- Модули не регистрируются напрямую. Регистратор рекурсивно обходит
  указанный модуль и все его дочерние модули, и регистрирует в реестре
  все классы и фабрики из каждого модуля.
```python 
import os
# будут зарегистрированы os и os.path но не sys
container.register(os)
```

Метод `register` у контейнера является классом `Registrator`, реализация 
контейнера не подразумевает прямого оперирования объектом из вне.

### add_settings
Добавляет или обновляет настройки контейнера. Ключом является класс, 
значение - настройки.
В роле настроек выступает объект класса [`Settings`](#Settings):
- [`init`](#init) используется для передачи простых объектов (чисел, строк).
- [`factory`](#factory) описывает способ создания объекта (фабрика, класс, абстрактный класс).
- [`scope`](#scope) регулирует жизненны цикл объекта, возможные значения указанны в константах текущего пакета:
    SINGLETON, TRANSIENT
- [`instance`](#instance) создания настроек с готовым объектом при разрешении
    зависимостей

```python
from abc import ABC, abstractmethod
from classic.container import container


class Interface(ABC):

    @abstractmethod
    def method(self): ...


class Implementation(Interface):

    def method(self):
        return 1


class Composition:

    def __init__(self, impl: Interface):
        self.impl = impl


class NextLevelComposition:

    def __init__(self, obj: Composition):
        self.obj = obj


def composition_factory(obj: Interface) -> Composition:
    return Composition(obj)


container.register(
    composition_factory, Implementation, Composition, NextLevelComposition
)

container.add_settings({
    Interface: container.factory(Implementation),
    Composition: container.factory(composition_factory)
})

resolved = container.build(NextLevelComposition)
```
Подробное описание в классе Settings

### reset
Удаляет добавленные настройки контейнера и ссылки на инстансы уже 
созданных классов. Подразумевается использование в тестировании.

```python
from dataclasses import dataclass
from classic.container import container


class SomeCls:
    pass


@dataclass
class AnotherCls:
    some: SomeCls


result_1 = container.build(AnotherCls)
container.reset()
result_2 = container.build(AnotherCls)

result_1 is not result_2
```
### resolve
Разрешает зависимости для указанной реализации, создает и возвращает инстанс класса.

Рекурсивно обходит дерево зависимостей, начиная с указанного класса.
На каждый шаг рекурсии для указанного класса ищется фабрика в реестре.
Далее для найденной фабрики собираются аргументы,
чтобы вызвать фабрику и построить объект.
При этом:
 - пропускаются аргументы простых типов, аргументы без аннотаций
   и функции;
 - подставляются значения из init для аргументов,
   указанных в этом же init;
 - для аргументов, проаннотированных классами, повторяется рекурсия.

В процессе разрешения могут возникать ситуации, когда:
 - для интерфейса (абстрактного класса) не нашлось реализации;
 - для класса нашлось больше 1 фабрики
   и ни одна не указана в настройках для этого класса;
 - фабрика для аргумента вернула None
   и для аргумента не указан значение по умолчанию;
 - при вызове фабрики не был указан обязательный аргумент.
Во всех этих случаях контейнер выкидывает ResolutionError.

Все ошибки состоят из двух частей. Первая часть уникальна для ошибки
и объясняет причину, во второй части описано,
что и в каком порядке пытался построить контейнер.
Она состоит из строк, по три элемента в каждой:
 - Target: полное имя класса (some.module.SomeClass);
 - Factory: полное имя фабрики (another.module.SomeFactory);
 - Arg: имя аргумента фабрики.

Пример:

```python 
from abc import ABC, abstractmethod
from classic.container import container


class Interface(ABC):

    @abstractmethod
    def method(self): ...


class Implementation(Interface):

    def __init__(self):
        raise NotImplemented

    def method(self):
        return 1


class Composition:

    def __init__(self, impl: Interface):
        self.impl = impl


class SomeClass:

    def __init__(self, obj: Composition):
        self.obj = obj


container.register(Interface, Implementation, SomeClass, Composition)
container.build(SomeClass)
```
```python 
classic.container.exceptions.ResolutionError: Class \
<class 'example.Interface'> do not have registered implementations.
Resolve chain:
Target: app.SomeClass, Factory: app.SomeClass, Arg: obj
Target: app.Composition, Factory: app.Composition, Arg: impl
Target: app.Interface, Factory: app.Implementation, Arg: -
```

Метод `resolve` у контейнера является классом `Resolver`, реализация 
контейнера не подразумевает прямого оперирования объектом из вне.

## Settings
Класс хранит настройки resolv-а контейнера.

Используется для хранения способа создания объекта или самого объекта
при разрешении зависимостей. 
### init
Позволяет установить значения аргументов для фабрики при построении объекта. 
Самое частое использование - передача простых объектов (чисел, строк).
```python 
from classic.container import Container, Settings, init

class SomeClass:
    def __init__(self, some_value: int):
        # Для int будет неудобно указывать фабрику,
        # так как много у каких классов может быть параметр типа int
        # (справедливо для любого простого типа), поэтому
        # библиотека оставляет возможность
        # указать параметр через init
        self.some_value = some_value

container = Container()

container.register(SomeClass)

# Длинный способ через конструктор
container.add_settings({
    SomeClass: Settings(init=dict(some_value=2))
})

# Вызов "цепочкой"
container.add_settings({
    SomeClass: Settings().init(some_value=2)
})

# А можно через алиас
container.add_settings({SomeClass: init(some_value=2)})
```
### factory
Позволяет явно передать способ создания компонента системы.
Значением может являться любой вызываемый объект возвращающий инстанс любого 
объекта, и имеющий аннотацию типов.
```python
from abc import ABC, abstractmethod
from classic.container import Container, Settings, factory

class Interface(ABC):

    @abstractmethod
    def method(self): ...

class Implementation(Interface):

    def method(self):
        return 1

class SomeClass:

    def __init__(self, impl: Interface):
        self.impl = impl

def composition_factory(obj: Interface) -> SomeClass:
    return SomeClass(obj)

container = Container()

container.register(Implementation, SomeClass, composition_factory)

# Длинный способ через конструктор
container.add_settings({
    SomeClass: Settings(factory=composition_factory)
})

# Вызов "цепочкой"
container.add_settings({
    SomeClass: Settings().factory(factory=composition_factory)
})

# А можно через алиас
container.add_settings({SomeClass: factory(composition_factory)})
```
### scope
Данная настройка регулирует жизненны цикл объекта, который может быть 
SINGLETON и TRANSIENT.

При значении SINGLETON контейнер создаст объект только один раз,
все последующие запросы будут использовать тот же самый объект.
Является значением по умолчанию.

При TRANSIENT контейнер будет создавать новый объект при каждом resolve.

Для каждого класса настройка scope добавляется отдельно!
```python
from abc import ABC, abstractmethod
from classic.container import Container, Settings, TRANSIENT, scope

class Interface(ABC):

    @abstractmethod
    def method(self): ...

class Implementation(Interface):

    def method(self):
        return 1

container = Container()

container.register(Interface, Implementation)

# Длинный способ через конструктор
container.add_settings({Implementation: Settings(scope=TRANSIENT)})

# Вызов "цепочкой"
container.add_settings({
    Implementation: Settings().scope(name=TRANSIENT)
})

# А можно через алиас
container.add_settings({Implementation: scope(TRANSIENT)})
```

### instance
Настройка позволяет подать готовый инстанс класса.

Подразумевается основное использование при потребности подачи
в разные классы готовых объектов, но настроенных по-разному.

Класс сделан для удобства, тоже самое можно сделать через фабрики.
```python
from abc import ABC, abstractmethod
from classic.container import Container, Settings, instance

class Interface(ABC):
    some_value: int

    @abstractmethod
    def method(self): ...

class Implementation(Interface):

    def __init__(self, some_value):
        self.some_value = some_value

    def method(self):
        return 1

class SomeClass:

    def __init__(self, impl: Interface):
        self.impl = impl

container = Container()

container.register(
    Interface, Implementation, SomeClass,
)

impl = Implementation(1)

# Длинный способ через конструктор
container.add_settings({
    SomeClass: Settings(instance=impl)
})

# Вызов "цепочкой"
container.add_settings({
    SomeClass: Settings().instance(instance=impl)
})

# А можно через алиас
container.add_settings({SomeClass: instance(impl)})
```
