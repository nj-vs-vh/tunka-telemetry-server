# Телеметрия в эксперименте Тунка

## Работа с сервером

### Конфигурация и данные

Корневая директория приложения камеры: `/home/vmn/camera-server/`

Конфигурация камеры: `camconfig.yaml`, инструкции прямо внутри, изменения в файле подгружаются и применяются на лету, без перезапуска приложения.

Изображения сохраняются в `images`, данные телеметрии, читаемые с Arduino -- в `observation-conditions-logs`.

### Запуск и логи

Базовые команды для запуска/остановки/перезапуска приложения

```bash
sudo systemctl status camserver-backend
sudo systemctl start camserver-backend
sudo systemctl stop camserver-backend
sudo systemctl restart camserver-backend
```

Логи хранятся в нескольких местах:

1. Логи приложения пишутся в `camserver.log`. Их уровень достаточно гибко настраивается в `backend/.env`. Можно логгировать работу асинхронного протокола камеры (`DEBUG_CAMERA_LOCK`) а также конфигурировать логи `pyindigo`.
2. Нативные логи Indigo. Уровень конфигурируется там же в `backend/.env`, пишутся в stdout и доступны по командам

```bash
# последние 50 записей
journalctl -u camserver-backend.service -n 50
# следить в режиме реального времени, например при запуске сервера
journalctl -u camserver-backend.service -f
```

Для самой подробной конфигурации работы сервера может понадобиться править

* Конфигруацию сервиса бэкенда: `/etc/systemd/system/camserver-backend.service`


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
