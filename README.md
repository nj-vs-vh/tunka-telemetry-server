# Телеметрия в эксперименте Тунка

## Работа с сервером

Корневая директория приложения: `/home/vmn/tunka-telemetry-server/`
Скрипт для запуска вручную: `/home/vmn/run_camserver_backend.sh`. Требуется запускать из-под root.

### Конфигурационные файлы

Конфигурация камеры: `camconfig.yaml`. Пояснения для полей можно найти в [примере](camconfig.yaml.example).
Изменения в этом файле подгружаются и применяются **без перезапуска приложения**.

Конфигурация сервера: `backend/.env`. Пример с пояснениями можно найти [здесь](backend/.env.example).

### Данные

В директорию `images` пишутся снимки неба, соответствующие сценарию `savetodisk` в `camconfig.yaml`. Данные телеметрии, читаемые с Arduino, в формате `.tsv` пишутся в директорию `observation-conditions-logs` (и также добавляются в виде заголовков в `.fits` файлы).

### Запуск и мониторинг

Приложение работает в `systemd`-сервисе:

```bash
sudo systemctl status camserver
sudo systemctl start camserver
sudo systemctl stop camserver
sudo systemctl restart camserver
```

Конфигурация сервиса: `/etc/systemd/system/camserver.service`

### Логи

Логи хранятся в нескольких местах:

1. `backend/camera.log` - основной лог приложения. Уровень логгирования различных модулей настраивается в `.env`-файле
2. `backend/server.log` - лог ошибок сервера
3. Лог сервиса:

    ```bash
    sudo journalctl -u camserver-backend.service -n 50  # последние 50 записей
    sudo journalctl -u camserver-backend.service -f  # следить в режиме реального времени, например при запуске сервера
    ```

## Установка и настройка

1. Склонировать этот репозиторий
    ```bash
    git clone https://github.com/nj-vs-vh/tunka-telemetry-server.git camera-server
    ```

2. Создать и активировать виртуальное окружение
    ```bash
    python3 -m venv indgenv
    . /indgenv/bin/activate
    pip3 install -r requirements.txt
    ```

3. Установить [`pyindigo`](https://github.com/nj-vs-vh/pyindigo) — INDIGO-интерфейс для Python — как указано в README по ссылке. Для применения обновлений в этой библиотеке, затрагивающих только Python-фронтенд `pyindigo`, достаточно из корневой директории вызвать вспомогательный скрипт
    ```bash
    git clone git@github.com:nj-vs-vh/pyindigo.git pyindigo_source
    . update_pyindigo.sh
    ```

4. Сервер конфигурируется двумя файлами: `backend/.env` содержит общие настройки сервера, логгера и способ запуска камеры (симулятор или настоящая камера); `camconfig.yaml` содержит описание режимов работы со значениями выдержки, усиления и периода съёмки, флаги включения/выключения, подробное описание содержится прямо внутри файла. Сами конфигурации уникальны для разных машин, можно использовать `*.example` файлы как основу.

    ```bash
    cp backend/.env.example backend/.env
    cp camconfig.yaml.example camconfig.yaml
    # отредактировать файлы
    ```

## Камера

Модель камеры: ZWO ASI120MC-S
