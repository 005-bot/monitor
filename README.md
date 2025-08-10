<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Apache License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/005-bot/monitor/tree/master">
    <img src="assets/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">005 Бот - Монитор</h3>

  <p align="center">
    Сервис мониторинга отключений
    <br />
    <br />
    <a href="https://github.com/005-bot/monitor/issues/new?labels=bug">Сообщить о проблеме</a>
    &middot;
    <a href="https://github.com/005-bot/monitor/issues/new?labels=enhancement">Предложить функцию</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->

- [О проекте](#о-проекте)
  - [Используемые технологии](#используемые-технологии)
- [Начало работы](#начало-работы)
  - [Предварительные требования](#предварительные-требования)
  - [Установка](#установка)
- [Настройки](#настройки)
- [Использование](#использование)
- [Лицензия](#лицензия)
- [Контакты](#контакты)


<!-- ABOUT THE PROJECT -->
## О проекте

Сервис мониторинга — это решение на базе Python, которое выполняет периодический веб-скрейпинг страниц с информацией об отключениях, обнаруживает изменения и публикует уведомления через Redis PubSub.

Основные функции:

- Автоматический веб-скрейпинг страниц с информацией об отключениях
- Обнаружение изменений с использованием хэш-сравнения
- Интеграция с Redis PubSub для уведомлений в реальном времени
- Настраиваемые интервалы мониторинга и параметры хранения
- Контейнеризация с помощью Docker для простого развертывания

<p align="right">(<a href="#readme-top">в начало</a>)</p>

### Используемые технологии

Этот проект построен с использованием современных инструментов Python и технологий контейнеризации:

- [![Python][Python]][Python-url]
- [![Docker][Docker]][Docker-url]
- [![Pipenv][Pipenv]][Pipenv-url]
- [![Redis][Redis]][Redis-url]
- [![BeautifulSoup][BeautifulSoup]][BeautifulSoup-url]
- [![httpx][httpx]][httpx-url]
- [![Pydantic][Pydantic]][Pydantic-url]

<p align="right">(<a href="#readme-top">в начало</a>)</p>

<!-- GETTING STARTED -->
## Начало работы

Чтобы запустить локальную копию, следуйте этим простым шагам.

### Предварительные требования

- Docker и Docker Compose
- Python 3.11+ (для локальной разработки)
- Redis 7.0+ (или используйте Docker Compose)

### Установка

1. Клонируйте репозиторий
   ```sh
   git clone https://github.com/005-bot/monitor.git
   cd monitor
   ```

2. Запустите с помощью Docker Compose
   ```sh
   docker compose up --build
   ```

3. Для локальной разработки
   ```sh
   pipenv install
   pipenv run python -m app
   ```

<p align="right">(<a href="#readme-top">в начало</a>)</p>

## Настройки

Для настройки используются переменные окружения:

| Название            | Описание                              | По умолчанию                        |
| ------------------- | ------------------------------------- | ----------------------------------- |
| `REDIS__URL`        | URL Redis                             | `redis://localhost:6379`            |
| `SCRAPER__URL`      | URL страницы с отключениями           | `http://93.92.65.26/aspx/Gorod.htm` |
| `SCRAPER__INTERVAL` | Период проверки обновлений в секундах | `60`                                |
| `STORAGE__TTL_DAYS` | Время хранения хэшей записей в днях   | `5`                                 |
| `STORAGE__PREFIX`   | Префикс хранилища для ключей в Redis  | `bot-005`                           |
| `PUBLISHER__PREFIX` | Префикс очереди PubSub в Redis        | `bot-005`                           |

<p align="right">(<a href="#readme-top">в начало</a>)</p>

<!-- USAGE EXAMPLES -->
## Использование

Сервис мониторинга работает непрерывно, сканируя и отслеживая информацию об отключениях:

1. **Конфигурация**: Установите переменные окружения в файле docker-compose.yml или .env
2. **Мониторинг**: Сервис сканирует настроенный URL с регулярными интервалами
3. **Обнаружение изменений**: Новые отключения обнаруживаются с помощью сравнения хэшей
4. **Уведомления**: Изменения публикуются в Redis PubSub для последующей обработки

> Примечание: Перед скрейпингом убедитесь, что вы соблюдаете robots.txt и условия использования сайта, а также настраивайте разумные интервалы запросов.

<p align="right">(<a href="#readme-top">в начало</a>)</p>

<!-- LICENSE -->
## Лицензия

Распространяется по лицензии Apache 2.0. Подробнее см. в файле `LICENSE`.

<p align="right">(<a href="#readme-top">в начало</a>)</p>

<!-- CONTACT -->
## Контакты

Электронная почта: [help@005бот.рф](mailto:help@005бот.рф)  
Сайт: [005бот.рф](https://005бот.рф)

<p align="right">(<a href="#readme-top">в начало</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/005-bot/monitor.svg?style=for-the-badge
[contributors-url]: https://github.com/005-bot/monitor/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/005-bot/monitor.svg?style=for-the-badge
[forks-url]: https://github.com/005-bot/monitor/network/members
[stars-shield]: https://img.shields.io/github/stars/005-bot/monitor.svg?style=for-the-badge
[stars-url]: https://github.com/005-bot/monitor/stargazers
[issues-shield]: https://img.shields.io/github/issues/005-bot/monitor.svg?style=for-the-badge
[issues-url]: https://github.com/005-bot/monitor/issues
[license-shield]: https://img.shields.io/github/license/005-bot/monitor.svg?style=for-the-badge
[license-url]: LICENSE
[Python]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://www.python.org/
[Docker]: https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
[Pipenv]: https://img.shields.io/badge/pipenv-%23000000.svg?style=for-the-badge&logo=pipenv&logoColor=white
[Pipenv-url]: https://github.com/pypa/pipenv
[Redis]: https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white
[Redis-url]: https://redis.io/
[BeautifulSoup]: https://img.shields.io/badge/beautifulsoup-%23000000.svg?style=for-the-badge&logo=python&logoColor=white
[BeautifulSoup-url]: https://www.crummy.com/software/BeautifulSoup/
[httpx]: https://img.shields.io/badge/httpx-%23000000.svg?style=for-the-badge&logo=python&logoColor=white
[httpx-url]: https://github.com/encode/httpx/
[Pydantic]: https://img.shields.io/badge/pydantic-%23000000.svg?style=for-the-badge&logo=python&logoColor=white
[Pydantic-url]: https://docs.pydantic.dev/latest/
