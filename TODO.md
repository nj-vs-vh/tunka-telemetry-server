* Взаимодействие фронта с сервером при неподключенной/отключенной камере. Следует (а) сделать эндпоинт для проверки подключения и выдавать соответствующую заглушку, если камеры нет; на этот же эндпоинт можно ходить при ошибках ответа сервера; этот же эндпоинт может при некоторых условиях триггерить перезагрузку камеры (отчитываться ою отрицательном результате в духе перезагрузили индиго, камеры всё ещё нет, перезапустите сервер целиком (команда на это?), также проверьте физическое подключение камеры)

* pyindigo реулярно падает при загрузке или выгрузке. Следует настроить nginx на ретрай.

* Продумать повнимательнее вёрстку фронта: в будущем пригодится сайдбар, пока достаточно аккуратного хедера/футера в серых тонах, в футере надо написать что это сделал я :)