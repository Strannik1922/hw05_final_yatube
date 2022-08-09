# hw05_final

### Спринт 6 - Проект спринта: подписки на авторов
### hw05_final - Проект спринта: подписки на авторов, Яндекс.Практикум.
Покрытие тестами проекта Yatube из спринта 6 Питон-разработчика бекенда Яндекс.Практикум. Все что нужно, это покрыть тестами проект, в учебных целях. Реализована система подписок/отписок на авторов постов.
### Технологии
- Python 3.7
- Django==2.2.28

# Начало работы
### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Strannik1922/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:
```
python -m venv venv
```

```
source venv/Scripts/activate
```

Устанавливаем зависимости:
```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Применяем миграции:
```
python yatube/manage.py makemigrations
```

```
python yatube/manage.py migrate
```

Создаем супер пользователя:
```
python yatube/manage.py createsuperuser
```

[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)
