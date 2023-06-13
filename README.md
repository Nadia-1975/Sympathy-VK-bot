## Запуск программы:
1.	Установка необходимых библиотек:
``` 
    pip install vk_api
    pip install psycopg2
    pip install sqlalchemy
    pip install sqlalchemy_utils
``` 
2.	Данные для взаимодействия с базой и VK лежат в config.json
3.	Запуск через main.py
4.	Взаимодействие с ботом начинается после написания команды ‘привет’.
## Входные данные
•	 Id пользователя в ВК, для которого мы ищем пару. Сервис автоматически получает его при написании команды ‘привет’,
если информации недостаточно сервис дополнительно запрашивает её у пользователя.
## Список команд:
1.	‘привет’ - выдает пользователю первичную информацию для начала работы с сервисом.
2.	‘начать поиск’ - начать поиск пары по указанным критериям.
3.	‘показать избранных’ - выводит информацию из базы данных по избранным кандидатам.
4.	‘пока’ - завершение работы сервиса.
5.	Можно заносить кандидатов в список избранных, либо в черный список при ответе на вопросы бота.