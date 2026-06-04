from pymongo import MongoClient

# Создание клиента
client = MongoClient('localhost', 27017)

# Подключение к базе данных
db = client['UsersDB']