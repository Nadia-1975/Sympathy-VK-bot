from core import *

def main():
    if not database_exists(engine.url):
        create_database(engine.url)
    create_tables(engine)
    list_chosen = []
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                user_id = str(event.user_id)
                request = event.text.lower()
                if request == 'привет':
                    fill_user_table(combine_user_data(user_id))
                    write_msg(user_id,
                              "Привет! Я SympathyBot\n"
                              "Я ищу пару подходящую по критериям и добавляю в список избранных или "
                              "в черный список по вашему желанию.\n"
                              "Критерии: ваш город, возраст в промежутке от -3 лет до +3 лет "
                              "от вашего возраста.\n"
                              "Чтобы начать поиск введите команду 'начать поиск'.\n"
                              "Для вывода списка избранных введите команду 'показать избранных'.\n"
                              "Для завершения взаимодействия со мной напишите 'пока',"
                              " либо напишите 'нет' при вопросе о продолжении поиска."
                              , None)
                elif request in ['начать поиск', 'продолжить поиск', 'да']:
                    random_choice = []
                    get_random_user_data = get_random_user(combine_users_data(user_id), user_id)
                    random_choice.append(get_random_user_data)
                    fill_user_search_table([get_random_user_data], user_id)
                    if random_choice[0]['id'] not in list_chosen:
                        write_msg(user_id, {random_choice[0]['first_name'] + ' ' + random_choice[0]['last_name']},
                                  {','.join(get_photos_list(sort_by_likes(get_photos(random_choice[0]['id']))))})
                        write_msg(user_id, f"Ссылка на профиль:{random_choice[0]['vk_link']}", None)
                        write_msg(user_id, "Занести пользователя в список избранных? да/нет", None)
                        message_text = loop_bot()
                        if message_text == 'да':
                            write_msg(user_id, "Кандидат занесен в список избранных", None)
                            fill_white_list(random_choice)
                            list_chosen.append(random_choice[0]['id'])
                        elif message_text == 'нет':
                            write_msg(user_id, "Кандидат занесен в черный список", None)
                            fill_black_list(random_choice)
                            list_chosen.append(random_choice[0]['id'])
                        write_msg(user_id,
                                  "Продолжить поиск? (да/нет)\n"
                                  "Либо введите 'показать избранных' для вывода списка избранных."
                                  , None)
                    else:
                        continue

                elif request == 'показать избранных':
                    write_msg(user_id, f"{check_db_favorites(user_id)}", None)
                    write_msg(user_id, f"Продолжить поиск? да/нет", None)
                elif request in ['пока', 'нет']:
                    write_msg(user_id, "Спасибо. Всего доброго!", None)
                    break
                else:
                    write_msg(user_id, "Увы, я вас не понимаю... Попробуйте изменить запрос...", None)


main()
