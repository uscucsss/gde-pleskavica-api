import sqlite3
import os
from dotenv import load_dotenv
load_dotenv() # команда находит файл .env и загружает переменные из него
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response, Cookie, Depends
import hashlib

# настройка хэширования для паролей бд
# кодовое слово для проверки при регистрации 
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default_pass_if_env_missing")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pleskavica_v2.db")

app = FastAPI()

class DishUpdatePrice(BaseModel):
    price: int # Новая цена в динарах

class CafeCreate(BaseModel):
    name: str # Имя должно быть строкой текста
    address: str # Адрес тоже должен быть строкой текста
    lat: float # Широта (дробное число)
    lon: float # Долгота (дробное число)

class DishCreate(BaseModel):
    cafe_id: int # ID кафе, к которому будет привязано блюдо (целое число)
    title: str # название блюда 
    price: int # цена в динарах (целое число)

class UserLogin(BaseModel):
    username: str # вводит логин 
    password: str # вводит пароль

#при старте сервера создается бд и таблица для кафан Сербии
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

@app.on_event("startup")
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    # создание таблиц 
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cafes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT, 
    lat REAL,
    lon REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cafe_id INTEGER,
        title TEXT,
        price INTEGER,
        FOREIGN KEY (cafe_id) REFERENCES cafes (id)
    )''')

    # проверка пустая ли база и если да - наполняем тестовыми данными
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_exists = cursor.fetchone()

    if not admin_exists:
    # хэшируем пароль из .env
        hashed_admin_password = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("admin", hashed_admin_password)
        )

    cursor.execute(
            "INSERT INTO cafes (name, address, lat, lon) VALUES (?, ?, ?, ?)",
            ("Walter Cevapi", "Strahinjica Bana 57, Beograd", 44.8194, 20.4638)
        )

    cursor.execute(
            "INSERT INTO menu (cafe_id, title, price) VALUES (?, ?, ?)",
            (1, "Гурманская плескавица 300г", 450)
        )
print("База данных была пуста. Данные созданы.")
   
conn.commit()
conn.close()
    
# главная страница
@app.get("/")
def home():
    return {"message": "Добро пожаловать в API Где Плескавица! Сервер работает."}

# Новое окно: выдаем список кафан из бд в браузер
@app.post("/cafes")
def check_admin_session(session_id: str = Cookie(None)):
    if session_id is None or session_id != "super_secret_cookie":
        raise HTTPException(
            status_code=401, 
            detail="Доступ запрещен. Вы не авторизованы как администратор."
        )
    return session_id

def create_cafe(cafe: CafeCreate, admin_session = Depends(check_admin_session)):
    local_conn = sqlite3.connect(DB_PATH)
    cursor = local_conn.cursor()

    cursor.execute(
        "INSERT INTO cafes (name, address, lat, lon) VALUES (?,?,?,?)",
        (cafe.namem, cafe.address, cafe.lat, cafe.lon)
    )
    local_conn.commit()
    local_conn.close()

    return {"status": "success", "message": f"Кафе '{cafe.name}' успешно добавлено"}

    # через цикл проходимся по каждому кафе и ищем его меню
    for cafe in cafes_rows:
        cafe_dict = dict(cafe)
        # вытаскиваем блюда, которые привязаны через id кафе
        local_cursor.execute("SELECT id, title, price FROM menu WHERE cafe_id = ?", (cafe_dict["id"],))
        menu_rows = local_cursor.fetchall()

        # превращение блюда в список словарей и вкладываем внутрь кафе
        cafe_dict["menu"] = [dict(dish) for dish in menu_rows]


        # добавление готового кафе с его меню в общий результат
        result.append(cafe_dict)

    local_conn.close()

    return {"status": "success", "data": result}
    
@app.post("/menu")
def create_dish(dish: DishCreate):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()
    
    # Снова включаем железную проверку:
    local_cursor.execute("SELECT id FROM cafes WHERE id = ?", (dish.cafe_id,))
    cafe_exists = local_cursor.fetchone()
    
    if not cafe_exists:
        local_conn.close()
        raise HTTPException(status_code=404, detail=f"Кафе с ID {dish.cafe_id} не существует")
    
    # Если кафе есть — добавляем блюдо
    local_cursor.execute(
        "INSERT INTO menu (cafe_id, title, price) VALUES (?, ?, ?)",
        (dish.cafe_id, dish.title, dish.price)
    )
    local_conn.commit()
    local_conn.close()
    
    return {"status": "success", "message": f"Блюдо '{dish.title}' успешно добавлено в меню!"}

@app.put("/menu/{dish_id}")
def update_dish_price(dish_id: int, data: DishUpdatePrice):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    # проверка, существует ли блюдо с таким id
    local_cursor.execute("SELECT id, title FROM menu WHERE id = ?", (dish_id,))
    dish = local_cursor.fetchone()

    if not dish:
        local_conn.close()
        raise HTTPException(status_code=404, detail=f"Блюдо с ID {dish_id} не найдено в базе")
    
    # dish[1] - название блюда (title), которые мы достали из базы
    dish_title = dish[1]

    # Обновление цены в таблице menu
    local_cursor.execute(
        "UPDATE menu SET price = ? WHERE id = ?",
        (data.price, dish_id)
    )
    local_conn.commit()
    local_conn.close()

    return {"status": "success", "message": f"Цена для блюда '{dish_title}' успешно изменена на {data.price}!"}

@app.delete("/menu/{dish_id}")
def delete_dish(dish_id: int):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    # Проверка на существование блюда 
    local_cursor.execute("SELECT id, title FROM menu WHERE id = ?", (dish_id,))
    dish = local_cursor.fetchone()

    if not dish:
        local_conn.close()
        raise HTTPException(status_code=404, detail=f"Блюдо с ID {dish_id} не найдено")
    
    dish_title = dish[1]

    #удаление записи из таблицы menu
    local_cursor.execute("DELETE FROM menu WHERE id = ?", (dish_id,))

    local_conn.commit()
    local_conn.close()

    return {"status": "success", "message": f"Блюдо '{dish_title}' успешно удалено из базы данных!"}

@app.post("/login")
def login_user(user_data: UserLogin, response: Response):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    # ищем хэш пароля в базе 
    cursor.execute("SELECT password FROM users WHERE username = ?", (user_data.username,))
    row = cursor.fetchone()

    conn.close() # закрываем соединение после того, как забрали данные

    # проверка нашли ли пользователя 
    if row is None:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    db_password_hash = row[0] 

    # хэш введенного админом пароль для сравнения
    incoming_password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()

    # сверяем хэши 
    if incoming_password_hash != db_password_hash:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    # выдаем скрытый цифровой пропуск в куки браузера 
    response.set_cookie(
        key="session_id",
        value="super_secret_cookie",
        httponly=True,
        samesite="lax"
    )

    return {"status": "success", "message": f"Добро пожаловать, {user_data.username}!"}