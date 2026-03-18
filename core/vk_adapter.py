# core/vk_adapter.py
import logging
import json
import random
import requests
import os
from datetime import datetime
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from core import user, movie, db

logger = logging.getLogger('core.vk')

class VKAdapter:
    def __init__(self, token, group_id):
        self.group_id = group_id
        self.vk_session = vk_api.VkApi(token=token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, group_id)
        self.user_context = {}
        logger.info(f"✅ VK Adapter инициализирован для группы {group_id}")

    def get_main_menu(self):
        """Возвращает структуру главного меню"""
        return {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "🎲 Случайный фильм"
                        }
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "🔍 Поиск"
                        }
                    }
                ],
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "🎉 Премьеры"
                        }
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "👤 Мой профиль"
                        }
                    }
                ],
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "❓ Помощь"
                        }
                    }
                ]
            ]
        }

    def send_message(self, user_id, text, keyboard=None):
        """Отправляет сообщение пользователю VK"""
        params = {
            'user_id': user_id,
            'message': text,
            'random_id': random.randint(1, 2**31)
        }
        if keyboard:
            params['keyboard'] = json.dumps(keyboard, ensure_ascii=False)
        
        try:
            self.vk.messages.send(**params)
            logger.debug(f"Сообщение отправлено пользователю VK {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")

    def send_message_with_keyboard(self, user_id, text, keyboard=None):
        """Отправляет сообщение с клавиатурой"""
        self.send_message(user_id, text, keyboard)

    def send_message_with_photo(self, user_id, text, attachment, keyboard=None):
        """Отправляет сообщение с фото"""
        params = {
            'user_id': user_id,
            'message': text,
            'attachment': attachment,
            'random_id': random.randint(1, 2**31)
        }
        if keyboard:
            params['keyboard'] = json.dumps(keyboard, ensure_ascii=False)
        
        try:
            self.vk.messages.send(**params)
            logger.debug(f"Сообщение с фото отправлено пользователю VK {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения с фото: {e}")

    def get_user_info(self, user_id):
        """Получает информацию о пользователе VK"""
        try:
            users = self.vk.users.get(user_ids=user_id)
            if users:
                return users[0]
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
        return None

    def run(self):
        """Главный цикл обработки событий"""
        logger.info("🚀 VK Adapter запущен, ожидаем сообщения...")
        
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.handle_message(event)

    def handle_message(self, event):
        user_id = event.obj.message['from_id']
        text = event.obj.message['text'].strip().lower()
        
        # Проверяем, есть ли payload (нажатие на инлайн-кнопку)
        payload = event.obj.message.get('payload')
        if payload:
            try:
                payload_data = json.loads(payload)
                command = payload_data.get('command')
                
                # Обработка команд из payload
                if command == 'opinion':
                    movie_id = payload_data.get('movie_id')
                    year = payload_data.get('year')
                    self.handle_opinion(user_id, movie_id, year)
                    return
                elif command == 'filter_rating':
                    value = payload_data.get('value')
                    query = payload_data.get('query')
                    self.apply_filter(user_id, 'rating_range', value, query)
                    return
                elif command == 'filter_decade':
                    value = payload_data.get('value')
                    query = payload_data.get('query')
                    self.apply_filter(user_id, 'decade', value, query)
                    return
                elif command == 'reset_filters':
                    query = payload_data.get('query')
                    if user_id in self.user_context:
                        self.user_context[user_id]['filters'] = {}
                    self.handle_search(user_id, query)
                    return
                elif command == 'show_results':
                    query = payload_data.get('query')
                    self.show_search_results(user_id, query)
                    return
                elif command == 'movies_page':
                    page = payload_data.get('page')
                    query = payload_data.get('query')
                    self.show_movies_page(user_id, query, page)
                    return
                elif command == 'regenerate_opinion':
                    # Заглушка для свежего взгляда
                    self.send_message_with_keyboard(
                        user_id,
                        "🔄 Функция 'Свежий взгляд' пока в разработке для VK. Скоро будет!",
                        self.get_main_menu()
                    )
                    return
                elif command == 'back_to_menu':
                    self.send_message_with_keyboard(
                        user_id,
                        "🐾 Возвращаюсь в главное меню",
                        self.get_main_menu()
                    )
                    return    
                elif command == 'premiers_page':
                    page = payload_data.get('page')
                    if user_id in self.user_context:
                        self.user_context[user_id]['page'] = page
                    self.show_premiers_page(user_id)
                    return
                    
            except Exception as e:
                logger.error(f"Ошибка обработки payload: {e}")
        
        # Обработка команды /start
        if text in ['/start', 'начать', 'старт']:
            self.handle_start(user_id)
            return
        
        # Проверяем контекст (ожидание ввода)
        if user_id in self.user_context:
            context = self.user_context[user_id]
            if context.get('state') == 'awaiting_search':
                self.handle_search(user_id, text)
                return
        
        # Обработка кнопок главного меню по тексту
        if text == "🎲 случайный фильм":
            self.handle_random(user_id)
        elif text == "🔍 поиск":
            self.handle_search_prompt(user_id)
        elif text == "🎉 премьеры":
            self.handle_premiers(user_id)
        elif text == "👤 мой профиль":
            self.handle_profile(user_id)
        elif text == "❓ помощь":
            self.handle_help(user_id)
        # Обработка текстовых команд
        elif text in ['/person', 'поиск по актерам']:
            self.send_message_with_keyboard(
                user_id,
                "🔍 Поиск по актерам пока в разработке для VK. Используй /search для поиска по названию.",
                self.get_main_menu()
            )
        elif text in ['/faq', 'помощь']:
            self.handle_help(user_id)
        elif text in ['/profile', 'профиль']:
            self.handle_profile(user_id)
        else:
            self.send_message_with_keyboard(
                user_id,
                "🐾 Я не понимаю эту команду. Используй меню ниже или напиши /help.",
                self.get_main_menu()
            )

    def handle_start(self, user_id):
        """Обработка команды /start"""
        welcome_text = (
            "🐾 Гав! Я КиноИщейка в VK!\n\n"
            "Я помогу тебе найти фильмы и расскажу своё мнение о них.\n\n"
            "👇 Выбирай команду из меню ниже:"
        )
        self.send_message_with_keyboard(user_id, welcome_text, self.get_main_menu())

    def handle_help(self, user_id):
        """Обработка команды /help"""
        help_text = (
            "❓ Помощь по командам:\n\n"
            "🎲 Случайный фильм - /random\n"
            "🔍 Поиск по названию - /search\n"
            "🎉 Ожидаемые премьеры - /premiers\n"
            "👤 Мой профиль - /profile\n\n"
            "Скоро появятся:\n"
            "• Поиск по актерам\n"
            "• Свежий взгляд на мнение\n"
            "• Любимые фильмы"
        )
        self.send_message_with_keyboard(user_id, help_text, self.get_main_menu())

    def handle_random(self, user_id):
        """Обработка команды /random"""
        movie_data = movie.get_random_movie_from_db(min_rating=7.0)
        
        if not movie_data:
            self.send_message_with_keyboard(user_id, "😢 Не нашла фильмов. Попробуй позже.")
            return
        
        movie_details = movie.get_movie_details(movie_data['id'])
        card_text, attachment, keyboard = self.format_movie_card_vk(movie_details)
        
        if attachment:
            self.send_message_with_photo(user_id, card_text, attachment, keyboard)
        else:
            self.send_message_with_keyboard(user_id, card_text, keyboard)

    def handle_search_prompt(self, user_id):
        """Запрашивает название фильма для поиска"""
        self.user_context[user_id] = {'state': 'awaiting_search'}
        self.send_message_with_keyboard(
            user_id,
            "🔍 Введи название фильма для поиска:"
        )

    def handle_search(self, user_id, query):
        """Поиск фильмов и показ интерфейса с фильтрами"""
        if len(query) < 2:
            self.send_message_with_keyboard(user_id, "🐾 Введи хотя бы 2 символа для поиска.")
            return
        
        self.user_context[user_id] = {
            'state': 'search',
            'query': query,
            'filters': {}
        }
        
        total_count, has_more = movie.search_movies_with_filters(query, filters=None, count_only=True)
        
        if total_count == 0:
            self.send_message_with_keyboard(user_id, f"😢 По запросу '{query}' ничего не нашлось.")
            return
        
        full_list = movie.search_movies_with_filters(query, filters=None, count_only=False)
        self.user_context[user_id]['full_list'] = full_list
        
        text = f"🔍 Поиск: {query}\n\n"
        text += f"Найдено фильмов: {'>' if has_more else ''}{total_count}\n\n"
        text += "Используй фильтры для уточнения, затем нажми 'Показать карточки'"
        
        keyboard = self.get_filter_keyboard(query, {}, total_count, has_more)
        self.send_message_with_keyboard(user_id, text, keyboard)

    def get_filter_keyboard(self, query, filters, total_count, has_more):
        """Создаёт клавиатуру с фильтрами"""
        buttons = []
        
        # Строка с рейтингом
        rating_row = []
        current_rating = filters.get('rating_range')
        
        rating_options = [
            ('new', '🆕 Новинки'),
            ('5-6', '⭐5-6'),
            ('6-7', '⭐6-7'),
            ('7-8', '⭐7-8'),
            ('8-9', '⭐8-9'),
            ('9-10', '⭐9-10')
        ]
        
        for value, label in rating_options:
            if current_rating == value:
                label = f"✓ {label}"
            
            rating_row.append({
                "action": {
                    "type": "text",
                    "label": label[:40],
                    "payload": json.dumps({
                        "command": "filter_rating",
                        "value": value,
                        "query": query
                    })
                }
            })
            
            if len(rating_row) == 3:
                buttons.append(rating_row)
                rating_row = []
        
        if rating_row:
            buttons.append(rating_row)
        
        # Строка с десятилетиями
        decade_row = []
        current_decade = filters.get('decade')
        
        decade_options = [
            ('pre1980', '📽 До1980'),
            ('1980s', '📅1980-е'),
            ('1990s', '📅1990-е'),
            ('2000s', '📅2000-е'),
            ('2010s', '📅2010-е'),
            ('2020s', '📅2020-е')
        ]
        
        for value, label in decade_options:
            if current_decade == value:
                label = f"✓ {label}"
            
            decade_row.append({
                "action": {
                    "type": "text",
                    "label": label[:40],
                    "payload": json.dumps({
                        "command": "filter_decade",
                        "value": value,
                        "query": query
                    })
                }
            })
            
            if len(decade_row) == 3:
                buttons.append(decade_row)
                decade_row = []
        
        if decade_row:
            buttons.append(decade_row)
        
        # Кнопка показа результатов
        if total_count > 0:
            if has_more:
                button_text = f"🎬 Показать первые {total_count}"
            else:
                button_text = f"🎬 Показать карточки ({total_count})"
            
            buttons.append([{
                "action": {
                    "type": "text",
                    "label": button_text[:40],
                    "payload": json.dumps({
                        "command": "show_results",
                        "query": query
                    })
                }
            }])
        
        # Кнопка сброса
        if filters:
            buttons.append([{
                "action": {
                    "type": "text",
                    "label": "🔄 Сбросить фильтры",
                    "payload": json.dumps({
                        "command": "reset_filters",
                        "query": query
                    })
                }
            }])
        
        return {"buttons": buttons}

    def apply_filter(self, user_id, filter_type, value, query):
        """Применяет фильтр и обновляет интерфейс"""
        if user_id not in self.user_context:
            self.user_context[user_id] = {}
        
        filters = self.user_context[user_id].get('filters', {})
        
        if filters.get(filter_type) == value:
            filters.pop(filter_type, None)
        else:
            filters[filter_type] = value
        
        self.user_context[user_id]['filters'] = filters
        
        total_count, has_more = movie.search_movies_with_filters(
            query, 
            filters=filters if filters else None, 
            count_only=True
        )
        
        if total_count > 0:
            full_list = movie.search_movies_with_filters(
                query, 
                filters=filters if filters else None, 
                count_only=False
            )
            self.user_context[user_id]['full_list'] = full_list
        
        text = f"🔍 Поиск: {query}\n\n"
        if filters:
            text += "Активные фильтры:\n"
            if filters.get('rating_range'):
                text += f"• {filters['rating_range']}\n"
            if filters.get('decade'):
                text += f"• {filters['decade']}\n"
            text += "\n"
        
        text += f"Найдено фильмов: {'>' if has_more else ''}{total_count}\n\n"
        text += "Настрой фильтры и нажми 'Показать карточки'"
        
        keyboard = self.get_filter_keyboard(query, filters, total_count, has_more)
        self.send_message_with_keyboard(user_id, text, keyboard)

    def show_search_results(self, user_id, query):
        """Показывает результаты поиска по 5 фильмов"""
        if user_id not in self.user_context:
            self.send_message_with_keyboard(user_id, "😢 Начни поиск заново.")
            return
        
        full_list = self.user_context[user_id].get('full_list', [])
        if not full_list:
            self.send_message_with_keyboard(user_id, "😢 Нет фильмов для показа.")
            return
        
        self.show_movies_page(user_id, query, 0)

    def show_movies_page(self, user_id, query, page):
        """Показывает страницу с 5 фильмами"""
        if user_id not in self.user_context:
            return
        
        full_list = self.user_context[user_id].get('full_list', [])
        items_per_page = 5
        total_pages = (len(full_list) + items_per_page - 1) // items_per_page
        
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(full_list))
        
        header = f"📽 Результаты поиска '{self.user_context[user_id].get('query', '')}'\n"
        header += f"Страница {page+1} из {total_pages}\n\n"
        self.send_message_with_keyboard(user_id, header)
        
        for movie_data in full_list[start_idx:end_idx]:
            movie_details = movie.get_movie_details(movie_data['id'])
            card_text, attachment, card_keyboard = self.format_movie_card_vk(movie_details)
            if attachment:
                self.send_message_with_photo(user_id, card_text, attachment, card_keyboard)
            else:
                self.send_message_with_keyboard(user_id, card_text, card_keyboard)
        
        # Кнопки навигации + меню
        nav_buttons = []
        if page > 0:
            nav_buttons.append({
                "action": {
                    "type": "text",
                    "label": "⬅️ Предыдущая",
                    "payload": json.dumps({
                        "command": "movies_page",
                        "page": page-1,
                        "query": query
                    })
                }
            })
        
        if page < total_pages - 1:
            nav_buttons.append({
                "action": {
                    "type": "text",
                    "label": "Следующая ➡️",
                    "payload": json.dumps({
                        "command": "movies_page",
                        "page": page+1,
                        "query": query
                    })
                }
            })
        
        # Всегда добавляем кнопку "В меню"
        nav_buttons.append({
            "action": {
                "type": "text",
                "label": "🏠 В меню",
                "payload": json.dumps({
                    "command": "back_to_menu"
                })
            }
        })
        
        # Разбиваем на строки по 2 кнопки
        rows = []
        for i in range(0, len(nav_buttons), 2):
            rows.append(nav_buttons[i:i+2])
        
        keyboard = {"buttons": rows}
        self.send_message_with_keyboard(user_id, "👇 Что дальше?", keyboard)

    def handle_premiers(self, user_id):
        """Обработка команды /premiers"""
        premiers_list = movie.get_premier_movies_from_db()
        
        if not premiers_list:
            self.send_message_with_keyboard(user_id, "😢 Сейчас нет ожидаемых премьер.")
            return
        
        self.user_context[user_id] = {
            'state': 'premiers',
            'movies': premiers_list,
            'page': 0
        }
        
        self.show_premiers_page(user_id)

    def show_premiers_page(self, user_id):
        """Показывает страницу с премьерами"""
        if user_id not in self.user_context:
            return
        
        movies = self.user_context[user_id].get('movies', [])
        page = self.user_context[user_id].get('page', 0)
        
        items_per_page = 5
        total_pages = (len(movies) + items_per_page - 1) // items_per_page
        
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(movies))
        
        header = f"🎉 Ожидаемые премьеры\nСтраница {page+1} из {total_pages}\n\n"
        self.send_message_with_keyboard(user_id, header)
        
        for movie_data in movies[start_idx:end_idx]:
            movie_details = movie.get_movie_details(movie_data['id'])
            card_text, attachment, card_keyboard = self.format_movie_card_vk(movie_details)
            if attachment:
                self.send_message_with_photo(user_id, card_text, attachment, card_keyboard)
            else:
                self.send_message_with_keyboard(user_id, card_text, card_keyboard)
        
        # Кнопки навигации + меню
        nav_buttons = []
        if page > 0:
            nav_buttons.append({
                "action": {
                    "type": "text",
                    "label": "⬅️ Предыдущая",
                    "payload": json.dumps({
                        "command": "premiers_page",
                        "page": page-1
                    })
                }
            })
        
        if page < total_pages - 1:
            nav_buttons.append({
                "action": {
                    "type": "text",
                    "label": "Следующая ➡️",
                    "payload": json.dumps({
                        "command": "premiers_page",
                        "page": page+1
                    })
                }
            })
        
        # Всегда добавляем кнопку "В меню"
        nav_buttons.append({
            "action": {
                "type": "text",
                "label": "🏠 В меню",
                "payload": json.dumps({
                    "command": "back_to_menu"
                })
            }
        })
        
        # Разбиваем на строки по 2 кнопки
        rows = []
        for i in range(0, len(nav_buttons), 2):
            rows.append(nav_buttons[i:i+2])
        
        keyboard = {"buttons": rows}
        self.send_message_with_keyboard(user_id, "👇 Навигация:", keyboard)

    def format_movie_card_vk(self, movie):
        """Форматирует карточку фильма для VK с постером"""
        if not movie:
            return "😢 Информация о фильме недоступна", None, None
        
        title = movie.get('name', 'Без названия')
        year = movie.get('year', '')
        is_new = movie.get('is_new_release', False)
        movie_id = movie.get('id', '')
        
        year_display = f"{year} 🆕" if is_new else f"{year}"
        
        content_type = movie.get('movie_type', 'movie')
        type_mapping = {
            'movie': 'фильм',
            'tv-series': 'сериал',
            'mini-series': 'мини-сериал',
            'cartoon': 'мультфильм'
        }
        type_text = type_mapping.get(content_type, 'фильм')
        
        rating = movie.get('rating', 'отсутствует')
        if rating and isinstance(rating, (int, float)):
            rating = round(rating, 1)
        
        countries = ', '.join(movie.get('countries', [])) if movie.get('countries') else 'отсутствует'
        genres = ', '.join(movie.get('genres', [])) if movie.get('genres') else 'отсутствует'
        
        # Описание
        description = movie.get('description')
        if not description or description == 'null' or description == 'None':
            description = 'Описание отсутствует'
        elif len(description) > 800:
            description = description[:800] + '...'
        
        directors_list = []
        for director in movie.get('directors', [])[:2]:
            name = director.get('name') or director.get('enName')
            if name:
                directors_list.append(name)
        directors = ', '.join(directors_list) if directors_list else 'неизвестен'
        
        actors_list = []
        for actor in movie.get('actors', [])[:5]:
            name = actor.get('name') or actor.get('enName')
            if name:
                actors_list.append(name)
        actors = ', '.join(actors_list) if actors_list else 'не указаны'
        
        premiere_info = ""
        if is_new or movie.get('is_new_release'):
            premiere_russia = movie.get('premiere_russia')
            premiere_world = movie.get('premiere_world')
            await_count = movie.get('await_count', 0)
            
            def format_date(date_str):
                if not date_str:
                    return 'отсутствует'
                try:
                    if 'T' in date_str:
                        return date_str.split('T')[0]
                    return date_str[:10]
                except:
                    return 'отсутствует'
            
            premiere_info = (
                f"\n🎉 Премьера РФ: {format_date(premiere_russia)}\n"
                f"🌎 Премьера Мир: {format_date(premiere_world)}\n"
                f"👥 Ожидают: {int(await_count) if await_count else 0} чел."
            )
        
        poster_url = movie.get('poster_url')
        
        text = (
            f"🎬 {title} ({year_display})\n"
            f"📁 Тип: {type_text}\n"
            f"⭐ Рейтинг КП: {rating}\n"
            f"🌍 Страна: {countries}\n"
            f"🎭 Жанр: {genres}\n"
            f"{premiere_info}\n"
            f"📝 {description}\n"
            f"🎥 Режиссер: {directors}\n"
            f"👥 Актеры: {actors}\n\n"
            f"🔗 Кинопоиск: https://www.kinopoisk.ru/film/{movie_id}/"
        )
        
        keyboard = {
            "buttons": [[
                {
                    "action": {
                        "type": "text",
                        "label": "🤔 Мнение",
                        "payload": json.dumps({
                            "command": "opinion",
                            "movie_id": movie_id,
                            "year": year
                        })
                    }
                }
            ]]
        }
        
        # Загружаем постер только если URL валидный
        attachment = None
        if poster_url and poster_url != 'None' and isinstance(poster_url, str) and poster_url.startswith('http'):
            attachment = self.upload_poster(poster_url)
        
        return text, attachment, keyboard

    def get_opinion(self, movie_id):
        """Получает мнение о фильме из БД"""
        with db.DB_LOCK:
            conn = db.get_opinions_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM movie_opinions WHERE movie_id = ?', 
                    (int(movie_id),)
                )
                return cursor.fetchone()
            except Exception as e:
                logger.error(f"Ошибка получения мнения: {e}")
                return None
            finally:
                conn.close()

    def generate_opinion(self, movie_details):
        """Генерирует мнение о фильме через OpenAI"""
        from openai import OpenAI
        import configparser
        import os
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.ini')
        
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        
        # Берем ключ из переменных окружения или конфига
        api_key = os.environ.get('OPENAI_API_KEY') or config['OpenAI']['api_key']
        base_url = config['OpenAI']['base_url']
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        title = movie_details.get('name', 'Без названия')
        year = movie_details.get('year', '')
        
        countries = movie_details.get('countries', [])
        countries_str = ', '.join(countries) if countries else 'неизвестно'
        
        genres = movie_details.get('genres', [])
        genres_str = ', '.join(genres) if genres else 'неизвестно'
        
        directors_list = movie_details.get('directors', [])
        if directors_list:
            director_names = []
            for director in directors_list:
                name = director.get('name') or director.get('enName')
                if name:
                    director_names.append(name)
            directors_str = ', '.join(director_names)
        else:
            directors_str = 'неизвестен'
        
        actors_list = movie_details.get('actors', [])[:7]
        if actors_list:
            actor_names = []
            for actor in actors_list:
                name = actor.get('name') or actor.get('enName')
                if name:
                    actor_names.append(name)
            actors_str = '\n'.join([f"• {name}" for name in actor_names])
        else:
            actors_str = 'не указаны'
        
        rating = movie_details.get('rating', 0)
        
        description = movie_details.get('description', 'Описание отсутствует')
        if description and len(description) > 800:
            description = description[:800] + '...'
        
        prompt = f"""Ты — КиноИщейка, собака-девочка, кинокритик с отличным чутьем на хорошее кино. Ты смотришь фильмы и делишься своим мнением с юмором и энтузиазмом. Говори о себе в женском роде.

Информация о фильме:
🎬 Название: {title} ({year})
🌍 Страна: {countries_str}
🎭 Жанр: {genres_str}
🎥 Режиссер: {directors_str}
⭐ Рейтинг Кинопоиска: {rating}
👥 В главных ролях:
{actors_str}

📝 Сюжет:
{description}

Требования к ответу:
1. Объем: 10-12 предложений
2. Без markdown-разметки
3. Только обычный текст
4. Разделяй части мнения переносами строк
5. Добавь собачий юмор
6. Говори о себе в женском роде
7. НЕ используй вводные фразы типа "Я посмотрела фильм и вот что думаю" - сразу начинай с содержательной части

Расскажи о:
- Настроении и смысле фильма
- Наградах (с учетом страны производства, если знаешь точно, а если нет - просто не упоминай, не выдумывай!)
- Особенностях
- Почему стоит посмотреть
- Плюсах и минусах

В конце обязательно добавь:
Оценка: от 5 до 10 (краткий комментарий почему)

После оценки добавь:
Настроение: 5 хэштегов (например #Радость #Грусть)
Атмосфера: 5 хэштегов (например #Мрачность #Яркость)"""

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты — КиноИщейка, собака-девочка, кинокритик. Твои ответы должны быть дружелюбными, с юмором, но при этом информативными. Обязательно используй женский род: 'я посмотрела', 'мне понравилось', 'я нашла' и т.д."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                stream=False,
                timeout=60
            )

            full_response = response.choices[0].message.content
            
            short_opinion = ""
            mood_tags = ""
            atmosphere_tags = ""
                         
            for part in full_response.split('\n'):
                if part.startswith("Оценка:"):
                    short_opinion = part
                elif part.startswith("Настроение:"):
                    mood_tags = part.replace("Настроение:", "").strip()
                elif part.startswith("Атмосфера:"):
                    atmosphere_tags = part.replace("Атмосфера:", "").strip()
            
            logger.info(f"✅ Сгенерировано мнение для фильма {title} ({year})")
            
            return {
                'full_opinion': full_response,
                'short_opinion': short_opinion,
                'mood_tags': mood_tags,
                'atmosphere_tags': atmosphere_tags
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации мнения: {e}")
            return None

    def handle_opinion(self, user_id, movie_id, year):
        """Обработка запроса мнения о фильме"""
        
        movie_details = movie.get_movie_details(int(movie_id))
        if not movie_details:
            self.send_message_with_keyboard(
                user_id, 
                "😢 Не могу найти этот фильм в базе.",
                self.get_main_menu()
            )
            return
        
        title = movie_details.get('name', 'Без названия')
        year = movie_details.get('year', '')
        kp_url = f"https://www.kinopoisk.ru/film/{movie_id}/"
        vk_group = "vk.com/movie_dog"
        
        existing = self.get_opinion(movie_id)
        
        if existing:
            _, short, full, mood, atmos, created = existing
            text = f"🎬 {title} ({year})\n🔗 {kp_url}\n\n{full}\n\n🐾\n\n👉 {vk_group}"
            self.send_message_with_keyboard(user_id, text, self.get_main_menu())
            
            # Добавляем инлайн-кнопки после мнения
            opinion_keyboard = {
                "inline": True,
                "buttons": [[
                    {
                        "action": {
                            "type": "text",
                            "label": "🔄 Свежий взгляд",
                            "payload": json.dumps({
                                "command": "regenerate_opinion",
                                "movie_id": movie_id,
                                "year": year
                            })
                        }
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "🐾 В меню",
                            "payload": json.dumps({
                                "command": "back_to_menu"
                            })
                        }
                    }
                ]]
            }
            self.send_message_with_keyboard(user_id, "👇 Что дальше?", opinion_keyboard)
            return
        
        self.send_message_with_keyboard(
            user_id,
            f"🎬 {title} ({year})\n🔗 {kp_url}\n\n🎬 Смотрю фильм в ускоренном режиме... это займёт несколько секунд.",
            None
        )
        
        opinion = self.generate_opinion(movie_details)
        
        if opinion:
            self.save_opinion(
                movie_id=movie_id,
                short_opinion=opinion['short_opinion'],
                full_opinion=opinion['full_opinion'],
                mood_tags=opinion['mood_tags'],
                atmosphere_tags=opinion['atmosphere_tags']
            )
            
            text = f"🎬 {title} ({year})\n🔗 {kp_url}\n\n{opinion['full_opinion']}\n\n🐾\n\n👉 {vk_group}"
            self.send_message_with_keyboard(user_id, text, self.get_main_menu())
            
            # Добавляем инлайн-кнопки после мнения
            opinion_keyboard = {
                "inline": True,
                "buttons": [[
                    {
                        "action": {
                            "type": "text",
                            "label": "🔄 Свежий взгляд",
                            "payload": json.dumps({
                                "command": "regenerate_opinion",
                                "movie_id": movie_id,
                                "year": year
                            })
                        }
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "🐾 В меню",
                            "payload": json.dumps({
                                "command": "back_to_menu"
                            })
                        }
                    }
                ]]
            }
            self.send_message_with_keyboard(user_id, "👇 Что дальше?", opinion_keyboard)
        else:
            self.send_message_with_keyboard(
                user_id,
                f"🎬 {title} ({year})\n🔗 {kp_url}\n\n😢 Что-то пошло не так. Попробуй позже.",
                self.get_main_menu()
            )

    def save_opinion(self, movie_id, short_opinion, full_opinion, mood_tags, atmosphere_tags):
        """Сохраняет мнение о фильме"""
        with db.DB_LOCK:
            conn = db.get_opinions_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO movie_opinions 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    int(movie_id),
                    str(short_opinion),
                    str(full_opinion),
                    str(mood_tags),
                    str(atmosphere_tags),
                    datetime.now().isoformat()
                ))
                conn.commit()
                logger.info(f"Сохранено мнение для movie_id={movie_id}")
            except Exception as e:
                logger.error(f"Ошибка сохранения мнения: {e}")
                conn.rollback()
            finally:
                conn.close()

    def handle_profile(self, user_id):
        """Заглушка для профиля"""
        self.send_message_with_keyboard(
            user_id,
            "👤 Профиль пользователя пока в разработке. Скоро будет!\n\n"
            "Здесь ты сможешь увидеть:\n"
            "• Свои любимые фильмы\n"
            "• Историю поиска\n"
            "• Баланс косточек",
            self.get_main_menu()
        )

    def upload_poster(self, image_url):
        """Загружает постер в VK и возвращает attachment"""
        if not image_url or image_url == 'None' or not isinstance(image_url, str):
            logger.debug(f"Некорректный URL постера: {image_url}")
            return None
        
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                logger.debug(f"Постер не доступен по URL: {image_url}")
                return None
            
            temp_file = f"/tmp/poster_{random.randint(1000, 9999)}.jpg"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            upload_server = self.vk.photos.getMessagesUploadServer()
            
            with open(temp_file, 'rb') as f:
                upload_response = requests.post(
                    upload_server['upload_url'],
                    files={'photo': f}
                ).json()
            
            photo = self.vk.photos.saveMessagesPhoto(
                photo=upload_response['photo'],
                server=upload_response['server'],
                hash=upload_response['hash']
            )[0]
            
            os.remove(temp_file)
            
            return f"photo{photo['owner_id']}_{photo['id']}"
            
        except Exception as e:
            logger.error(f"Ошибка загрузки постера для URL {image_url}: {e}")
            return None
