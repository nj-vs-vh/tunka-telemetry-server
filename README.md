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

* Конфигурацию nginx (статические файлы фронтенда): `/etc/nginx/sites-enabled/camserver.nginx`

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



2. Установить [`pyindigo`](https://github.com/nj-vs-vh/pyindigo) — INDIGO-интерфейс для Python — как указано в README по ссылке. Для применения обновлений в этой библиотеке, затрагивающих только Python-фронтенд `pyindigo`, достаточно из корневой директории вызвать вспомогательный скрипт

```bash
. update_pyindigo.sh
```

3. Сервер конфигурируется двумя файлами: `backend/.env` содержит общие настройки сервера, логгера и способ запуска камеры (симулятор или настоящая камера); `camconfig.yaml` содержит описание режимов работы со значениями выдержки, усиления и периода съёмки, флаги включения/выключения, подробное описание содержится прямо внутри файла. Сами конфигурации уникальны для разных машин, но можно использовать `*.example` файлы как основу.

```bash
cp backend/.env.example backend/.env
cp camconfig.yaml.example camconfig.yaml
# отредактировать файлы
```

### Установка и настройка веб-интерфейса (Quart API и React фронтенда)

Эта памятка работает только в dev-окружении, нужно переписать этот гайд после билда!

7. API сконфигурировано так, чтобы запускаться командой от фронтенда:

```bash
cd frontend
npm run api
```

8. Дождаться, пока загрузится бэкенд (занимает около 5-6 секунд из-за включения камеры), и, собственно, запустить фронтенд

```bash
npm run
```

## Камера

Модель камеры: ZWO ASI120MC-S

Режим работы: подобрать на месте, рабочий вариант (Москва, температура 29 градусов), сумма 10 кадров по 10 секунд, усиление 3-4 (код INDI, максимум — 100). Варианты режимов: стриминг, эмуляция стриминга на уровне клиента, просто длинная экспозиция. Потребуются дарки в начале и в конце ночи (кадры при закрытой крышке). Нужен режим набора библиотеки дарков (в плохую ночь).

Хранение данных: накопление в течение определённого времени (напр. 5 минут), сохранение сумма/среднего за это время. При этом анализировать можно каждый кадр и сохранять данные анализа чаще (каждые 10 секунд). С точки зрения веб-интерфейса можно сохранять JPEG-превью.

### Получение данных с камеры

Используется фреймворк [INDIGO](https://github.com/indigo-astronomy/indigo), для камеры есть готовый [INDIGO-драйвер](https://github.com/indigo-astronomy/indigo/tree/master/indigo_drivers/ccd_asi), со стороны нашего приложения используется кастомный сервер на основе [примера](https://github.com/indigo-astronomy/indigo/blob/master/indigo_examples/dynamic_driver_client.c), снабжённый интерфейсом для вызова из Python в виде объекта-адаптера.

Использование из кода: TODO

### Обработка данных с камеры

1. Угловые харакетристики камеры (tx, ty для каждого пикселя) — измерить в лаборатории.

2. Привязка поля зрения камеры к небесной сфере по известным ярким звёздам.

3. Оверлей с положениями звёзд, созвездий, координатной сеткой.

4. Выделение облаков — разбираемся на месте, сложно предсказать заранее.

## Прочая телеметрия

TODO

## Веб-интерфейс

TODO
