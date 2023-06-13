import os
import sys
import json
import random
from random import randrange
import datetime
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from database import create_tables, drop_tables, User, UserOfferData, WhiteList, BlackList
from sqlalchemy.exc import IntegrityError, InvalidRequestError, PendingRollbackError

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# считываем учетные данные базы, токены для бота и пользователя
with open(r'<path_to_config>\config.json', 'r') as config_file:
    config_dict = json.load(config_file)

db_type = config_dict['db_params']['db_type']
db_login = config_dict['db_params']['login']
db_password = config_dict['db_params']['password']
db_hostname = config_dict['db_params']['host']
db_port = config_dict['db_params']['port']
db_name = config_dict['db_params']['database']
bot_token = config_dict['bot_params']['group_token']
user_token = config_dict['bot_params']['user_token']

url_obj = f'{db_type}://{db_login}:{db_password}@{db_hostname}:{db_port}/{db_name}'
engine = create_engine(url_obj)

# создаем базу
if not database_exists(engine.url):
    create_database(engine.url)

# очищаем существующие таблицы
drop_tables(engine)

# создаем таблицы
create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

vk = vk_api.VkApi(token=bot_token)
vk2 = vk_api.VkApi(token=user_token)
longpoll = VkLongPoll(vk)


# механика взаимодействия с пользователем
def write_msg(user_id, message, attachment):
    vk.method('messages.send',
              {'user_id': user_id, 'message': message, 'attachment': attachment, 'random_id': randrange(10 ** 7)})


# механика считывания данных пользователя
def get_user_data(user_id):
    user_data = {}
    resp = vk.method('users.get', {'user_id': user_id,
                                   'v': 5.131,
                                   'fields': 'first name, last name, bdate, sex, city'})
    if resp:
        for key, value in resp[0].items():
            if key == 'city':
                user_data[key] = value['id']
            else:
                user_data[key] = value
    else:
        write_msg(user_id, 'Ошибка', None)
        return False
    return user_data


def check_missing_info(user_data):
    if user_data:
        for item in ['bdate', 'city']:
            if not user_data.get(item):
                user_data[item] = ''
        if user_data.get('bdate'):
            if len(user_data['bdate'].split('.')) != 3:
                user_data[item] = ''
        return user_data
    write_msg(user_data['id'], 'Ошибка', None)
    return False


# проверка даты рождения пользователя
def check_bdate(user_data, user_id):
    if user_data:
        for item_dict in [user_data]:
            if len(item_dict['bdate'].split('.')) != 3:
                write_msg(user_id, 'Введите дату рождения в формате "ДД.ММ.ГГГГ"', None)
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        user_data['bdate'] = event.text
                        return user_data
            else:
                return user_data
    write_msg(user_data['id'], 'Ошибка', None)
    return False


# проверка города пользователя
def city_id(city_name):
    resp = vk2.method('database.getCities', {
        'country_id': 1,
        'q': f'{city_name}',
        'need_all': 0,
        'count': 1000,
        'v': 5.131})
    if resp:
        if resp.get('items'):
            return resp.get('items')
        write_msg(city_name, 'Ошибка ввода города', None)
        return False


# проверка существующей записи города пользователя, заполняем автоматически если пустая запись
def check_city(user_data, user_id):
    if user_data:
        for item_dict in [user_data]:
            if item_dict['city'] == '':
                write_msg(user_id, 'Введите город:', None)
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        user_data['city'] = city_id(event.text)[0]['id']
                        return user_data
            else:
                return user_data
    write_msg(user_data['id'], 'Ошибка', None)
    return False


# считаем возраст пользователя
def get_age(user_data):
    if user_data:
        for key, value in user_data:
            user_data['age'] = datetime.datetime.now().year - int(user_data['bdate'][-4:])
            return user_data
    write_msg(user_data['id'], 'Ошибка', None)
    return False


# ищем пару в соответствии с параметрами пользователя
def user_search(user_data):
    resp = vk2.method('users.search', {
        'age_from': user_data['age'] - 3,
        'age_to': user_data['age'] + 3,
        'city': user_data['city'],
        'sex': 3 - user_data['sex'],
        'relation': 6,
        'status': 1,
        'has_photo': 1,
        'count': 1000,
        'v': 5.131})
    if resp:
        if resp.get('items'):
            return resp.get('items')
        write_msg(user_data['id'], 'Ошибка', None)
        return False


# фильтрация аккаунтов
def get_users_list(users_data, user_id):
    not_private_list = []
    if users_data:
        for person_dict in users_data:
            if person_dict.get('is_closed') == False:
                not_private_list.append(
                    {'first_name': person_dict.get('first_name'), 'last_name': person_dict.get('last_name'),
                     'id': person_dict.get('id'), 'vk_link': 'vk.com/id' + str(person_dict.get('id')),
                     'is_closed': person_dict.get('is_closed')
                     })
            else:
                continue
        return not_private_list
    write_msg(user_id, 'Ошибка', None)
    return False


# компановка пользовательских данных
def combine_user_data(user_id):
    user_data = [get_age(check_city(check_bdate(check_missing_info(get_user_data(user_id)), user_id), user_id))]
    if user_data:
        return user_data
    write_msg(user_id, 'Ошибка', None)
    return False


# компановка данных с найденных аккаунтов
def combine_users_data(user_id):
    users_data = get_users_list(
        user_search(get_age(check_city(check_bdate(check_missing_info(get_user_data(user_id)), user_id), user_id))),
        user_id)
    if users_data:
        return users_data
    write_msg(user_id, 'Ошибка', None)
    return False


# выбираем случайный аккаунт из полученного списка
def get_random_user(users_data, user_id):
    if users_data:
        return random.choice(users_data)
    write_msg(user_id, 'Ошибка', None)
    return False


# получаем фотографии
def get_photos(vk_id):
    resp = vk2.method('photos.getAll', {
        'owner_id': vk_id,
        'album_id': 'profile',
        'extended': 'likes',
        'count': 25
    })
    if resp:
        if resp.get('items'):
            return resp.get('items')
        write_msg(vk_id, 'Ошибка', None)
        return False


# сортировка фото по лайкам
def sort_by_likes(photos_dict):
    photos_by_likes_list = []

    for photos in photos_dict:
        likes = photos.get('likes')
        photos_by_likes_list.append([photos.get('owner_id'), photos.get('id'), likes.get('count')])
    photos_by_likes_list = sorted(photos_by_likes_list, key=lambda x: x[2], reverse=True)
    return photos_by_likes_list


# получение 3 самых популярных фото
def get_photos_list(sort_list):
    photos_list = []
    count = 0
    for photos in sort_list:
        photos_list.append('photo' + str(photos[0]) + '_' + str(photos[1]))
        count += 1
        if count == 3:
            return photos_list


# заполняем пользовательскую таблицу данными
def fill_user_table(user_data):
    if user_data:
        for item in user_data:
            user_record = session.query(User).filter_by(id=item['id']).scalar()
            if not user_record:
                user_record = User(id=item['id'])
            session.add(user_record)
            session.commit()
        return True
    write_msg(user_data['id'], 'Ошибка', None)
    return False


# заполняем таблицу найденными пользователями
def fill_user_search_table(users_data, user_id):
    try:
        for item in users_data:
            users_record = session.query(UserOfferData).filter_by(id=item['id']).scalar()
            if not users_record:
                users_record = UserOfferData(id=item['id'])
            session.add(users_record)
            session.commit()
        return True
    except (IntegrityError, InvalidRequestError, PendingRollbackError, TypeError):
        session.rollback()
        write_msg(user_id, 'Ошибка', None)
        return False


# заполняем таблицу избранного
def fill_white_list(random_choice):
    for item in random_choice:
        random_user_record = session.query(WhiteList).filter_by(id=item['id']).scalar()
        if not random_user_record:
            random_user_record = WhiteList(id=item['id'], first_name=item['first_name'], last_name=item['last_name'],
                                           vk_link=item['vk_link']
                                           )
        session.add(random_user_record)
    return session.commit()


# заполняем таблицу отсеянных пользователей (что бы не повторялись предложения)
def fill_black_list(random_choice):
    for item in random_choice:
        random_user_record = session.query(BlackList).filter_by(id=item['id']).scalar()
        if not random_user_record:
            random_user_record = BlackList(id=item['id'])
        session.add(random_user_record)
    return session.commit()


# выдаем список избранных пользователю
def check_db_favorites(user_id):
    db_favorites = session.query(WhiteList).order_by(WhiteList.user_id).all()
    all_users = []
    if db_favorites:
        for item in db_favorites:
            all_users.append(
                [item.user_id, 'id:' + str(item.id), item.first_name + ' ' + item.last_name, item.vk_link + ' '])
        return all_users
    write_msg(user_id, 'Ошибка', None)
    return False


# что бы бот продолжал писать сообщения после первого поиска (бесконечный цикл)
def loop_bot():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW:
            if this_event.to_me:
                message_text = this_event.text
                return message_text
