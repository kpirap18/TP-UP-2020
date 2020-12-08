"""
    Файл с описанием документов в базе данных
"""
import mongoengine


# Класс, описываюший пользователя
class User(mongoengine.Document):
    user_id = mongoengine.IntField(required=True)
    user_login = mongoengine.StringField(required=True, max_length=200)
    user_name = mongoengine.StringField(required=True, max_length=50)
    user_status = mongoengine.StringField(max_length=20)
    user_count_theme = mongoengine.IntField(required=True)
    user_number_theme = mongoengine.IntField(required=True)
    user_wrong_answer = mongoengine.StringField()
    user_wrong_answer_count = mongoengine.IntField()


# Класс, описывающий данные вопроса
class Theme2(mongoengine.Document):
    number = mongoengine.IntField(required=True)
    name = mongoengine.StringField(required=True, max_length=1000)
    theory = mongoengine.StringField(required=True, max_length=100000)
    text = mongoengine.ListField(mongoengine.StringField(required=True, max_length=500000))
    answers = mongoengine.ListField(mongoengine.ListField(mongoengine.StringField(required=True, max_lenght=50)))
    correct_answer = mongoengine.ListField(mongoengine.StringField(required=True, max_length=50000))
    task = mongoengine.StringField(required=True, max_length=500000)
    task_answer = mongoengine.StringField(required=True, max_length=300000)
