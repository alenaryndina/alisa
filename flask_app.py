from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)
import translate

logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

Session_data = {}
current_status = "start"
current_dialog = "start"


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    main_dialog(response, request.json)

    logging.info('Request: %r', response)

    return json.dumps(response)


q_num = 0


def main_dialog(res, req):
    global current_status, current_dialog, Session_data, q_num

    user_id = req['session']['user_id']
    if current_dialog == "start":
        if req['session']['new']:
            res['response']['text'] = 'Привет! Как тебя зовут? '
            Session_data[user_id] = {
                'suggests': [],
                'username': "Пользователь"
            }

            return
        if current_status == "start":
            name = get_first_name(req)
            if name  is None:
                name = "Незнакомец"
            Session_data[user_id]['username'] = name.title()

            res['response']['text'] = 'Приятно познакомиться, ' + Session_data[user_id]['username']
            current_status = "start2"

            res['response']['buttons'] = get_suggests(user_id)
            return
        if current_status == "start2":
            res['response']['text'] = Session_data[user_id]['username'] + '  О чем хочешь поговорить?'
            current_status = "start_question"
            Session_data[user_id]['suggests'] = [
                "Просто поболтать.",
                "Переведи текст.",
                "Вопросы по городам",
                "Покажи города",
                "Тест по географии",
            ]
            Session_data[user_id]['quest'] = ['Как погода?', 'Как тебя зовут?', 'Тебе много лет?', 'Чем занимаешься?']

            res['response']['buttons'] = get_suggests(user_id)
            return

        if current_status == "start_question":
            if req['request']['original_utterance'].lower() in ['просто поболтать.', 'поболтать', 'поговорим',
                                                                'поговорить', 'расскажи']:
                current_dialog = "talk"
                res['response']['text'] = 'Отлично! Как твои дела?'
                current_status = 'talk_alisa'
                return
            if req['request']['original_utterance'].lower() in ['Вопросы по городам']:
                current_dialog = "city"
                res['response'][
                    'text'] = 'Отлично! Я могу сказать в какой стране город или сказать расстояние между городами!'
                current_status = 'NONE'
                return
            if req['request']['original_utterance'].lower() in ['переведи текст.', 'переведи', 'переводчик',
                                                                'нужно перевести']:
                current_dialog = "translite"
                res['response']['text'] = 'Отлично! Что нужно перевести?'
                Session_data[user_id]['suggests'] = [
                    "Русский-английский",
                    "Английский-русский"
                ]
                res['response']['text'] = Session_data[user_id]['username'] + '. Выбери язык'
                res['response']['buttons'] = get_suggests(user_id)
                current_status = 'start'
                current_dialog = 'translite'

                return

            if req['request']['original_utterance'].lower() in ['тест по географии', 'география', 'тест']:
                current_dialog = "test"
                res['response']['text'] = Session_data[user_id]['username'] + ',начинаем тест'
                current_status = 1
                current_dialog = 'test'

                return
            if req['request']['original_utterance'].lower() in ['покажи города']:
                current_dialog = "gallery"
                res['response']['text'] = 'Отлично!'
                Session_data[user_id]['suggests'] = [
                    "Тамбов",
                    "Москва",
                    "Воронеж"
                ]
                res['response']['text'] = Session_data[user_id]['username'] + ', Какой город показать?'
                res['response']['buttons'] = get_suggests(user_id)
                current_status = 'start'
                current_dialog = 'gallery'

                return
    if current_dialog == "talk":
        talk_dialog(res, req)
        return
    if current_dialog == "translite":
        translite_dialog(res, req)
        return
    if current_dialog == 'city':
        city_dialog(res, req)
        return
    if current_dialog == 'gallery':
        gallery_dialog(res, req)
        return
    if current_dialog == 'test':
        test_dialog(res, req)
        return


result = 0


def test_dialog(res, req):
    global current_status, current_dialog, Session_data, lang, result
    user_id = req['session']['user_id']
    quest = [(1, "Название науки «география» означает? ", "Описание Земли"),
             (2, "География как наука зародилась в Древнем(ей)?", "Греции "),
             (3, "Ближайшая к Солнцу планета? ", "Меркурий "),
             (4, "Легкий ветер, дующий на побережье и меняющий направление 2 раза в сутки? ", "Бриз "),
             (5, "Самая большая низменность на земном шаре?", "Амазонская "),
             (6, "Горы, разделяющие Европу и Азию? ", "Уральские "),
             (7, "Самые высокие горы на Земле? ", "Гималаи"),
             (8, "Земная кора и часть верхней мантии образуют? ", "Литосферу"),
             (9, "Географическая широта полюсов равна? ", "90°"),
             (10, "Химическая осадочная горная порода? ", "Каменная соль ")]
    var_answer = [["Описание Земли", "Наука о почвах?", "История Земли"],
                  ["Египте", "Персии", "Греции "],
                  ["Венера", "Меркурий ", "Марс"],
                  ["Бриз ", "Муссоны", "Западные ветра"],
                  ["Прикаспийская", "Амазонская ", "Западно-Сибирская"],
                  ["Альпы", "Гималаи", "Уральские "],
                  ["Уральские", "Гималаи", "Альпы"],
                  ["Литосферу", "Гидросферу", "Атмосферу"],
                  ["120°", "90°", "180°"],
                  ["Кварцит ", "Каменная соль ", "Гранит"]]

    if current_status == len(quest) + 1:
        if current_status > 1:
            if req['request']['original_utterance'].lower() == quest[-1][2]:
                result += 1
        res['response']['text'] = "Отгадано " + str(result) + "  из " + str(len(quest))
        current_status = "start2"
        current_dialog = "start"
        return
    for i in range(len(quest)):

        if current_status == quest[i][0]:
            if current_status > 1:
                if req['request']['original_utterance'] == quest[i - 1][2]:
                    result += 1

            res_text = "Вопрос " + str(i) + " из " + str(len(quest)) + " (" + str(result) + ")"
            res['response']['text'] = quest[i][1] + " " + res_text
            Session_data[user_id]['suggests'] = var_answer[i]
            res['response']['buttons'] = get_suggests(user_id)
            current_status += 1

            return

    return


def talk_dialog(res, req):
    global current_status, current_dialog, Session_data, lang, q_num
    user_id = req['session']['user_id']

    if '?' in req['request']['original_utterance'].lower():
        current_status = 'talk_user'
    else:
        current_status = 'talk_alisa'
    if current_status == 'talk_alisa':
        Session_data[user_id]['quest'] = ['Как погода?', 'Тебе много лет?',
                                          'Чем занимаешься?', 'У тебя много друзей?',
                                          'Что тебя может сильно рассмешить?',
                                          'У тебя есть брат или сестра?', 'Чем занимаешься по жизни?',
                                          'Какой твой любимый фильм??',
                                          'Какое твое любимое блюдо?', 'Чего ты боишься больше всего?',
                                          'С кем ты живешь?']
        res['response']['text'] = Session_data[user_id]['quest'][q_num]
        q_num += 1

        if q_num >= len(Session_data[user_id]['quest']):
            res['response']['text'] = 'Не знаю, о чем еще спросить'

            current_dialog = "start"
            current_status = "start2"

        return

    elif current_status == 'talk_user':

        end_q = ['Что-нибудь еще спросишь?', 'Еще поговорим?', 'Что-то еще?']
        if 'погода' in req['request']['original_utterance'].lower():
            res['response']['text'] = 'Нормальная' + '. ' + random.choice(end_q)
            return
        if 'имя' in req['request']['original_utterance'].lower():
            res['response']['text'] = 'Алиса' + '. ' + random.choice(end_q)
            return
        if 'лет' in req['request']['original_utterance'].lower():
            res['response']['text'] = 'Не знаю. Мало. ' + '. ' + random.choice(end_q)
            return
        res['response']['text'] = 'Не понятно о чем ты'
        return
    else:
        res['response']['text'] = 'Ты неразговорчивый. Что-нибудь хочешь?'
        current_dialog = "start"
        current_status = "start2"
        return


lang = "ru-en"


def translite_dialog(res, req):
    global current_status, current_dialog, Session_data, lang
    logging.info(lang)
    user_id = req['session']['user_id']
    if current_status == "start":
        if req['request']['original_utterance'] == "Русский-английский":

            lang = 'ru-en'

        else:
            lang = 'en-ru'
        res['response']['text'] = Session_data[user_id]['username'] + " скажи текст"
        current_status = 'start_translite'
        return

    if 'хватит' in req['request']['original_utterance'].lower():
        current_dialog = 'start'
        res['response']['text'] = "Была рада помочь"
        current_status = 'start2'
        return
    if current_status == 'start_translite':
        res['response']['text'] = "Перевод: " + translate.translate(req['request']['original_utterance'], lang)[0]
        current_status = 'start_translite'
        return


def gallery_dialog(res, req):
    global current_status, current_dialog, Session_data
    if current_dialog == "gallery":
        cities = {
            'тамбов':
                '1652229/a4f54dca174a5e79ff1d'
            ,
            'москва':
                '1521359/53fc3bb34e2483f6794a'
            ,
            'воронеж':
                '1521359/0b2c34dc9f54dc235084'
            ,
            'нью-йорк':
                '1652229/728d5c86707054d4745f'
            ,
            'париж':
                '1652229/f77136c2364eb90a3ea8'

        }
        user_id = req['session']['user_id']

        city = req['request']['original_utterance'].lower()
        if city == "хватит":
            current_dialog = "start"
            current_status = "start"
            res['response']['text'] = 'Ок'
            return
        if city in cities:
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Этот город я знаю.'
            res['response']['card']['image_id'] = cities[city]
            res['response']['text'] = req['request']['original_utterance']
        else:
            res['response']['text'] = 'Первый раз слышу об этом городе.'
        return
    else:
        return


def city_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Я могу сказать в какой стране город или сказать расстояние между городами!'

        return

    cities = get_cities(req)

    if len(cities) == 0:

        res['response']['text'] = 'Ты не написал название не одного города!'

    elif len(cities) == 1:

        res['response']['text'] = 'Этот город в стране - ' + get_geo_info(cities[0], 'country')

    elif len(cities) == 2:

        distance = get_distance(get_geo_info(cities[0], 'coordinates'), get_geo_info(cities[1], 'coordinates'))
        res['response']['text'] = 'Расстояние между этими городами: ' + str(round(distance)) + ' км.'

    else:

        res['response']['text'] = 'Слишком много городов!'


def get_cities(req):
    cities = []

    for entity in req['request']['nlu']['entities']:

        if entity['type'] == 'YANDEX.GEO':

            if 'city' in entity['value'].keys():
                cities.append(entity['value']['city'])

    return cities


def get_first_name(req):

    for entity in req['request']['nlu']['entities']:

        if entity['type'] == 'YANDEX.FIO':

            return entity['value'].get('first_name', None)


def get_suggests(user_id):
    session = Session_data[user_id]
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests']
    ]
    Session_data[user_id] = session

    return suggests


if __name__ == '__main__':
    app.run()
