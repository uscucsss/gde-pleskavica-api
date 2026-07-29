import sqlite3
import os
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

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

#при старте сервера создается бд и таблица для кафан Сербии
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
# 1. СНАЧАЛА СОЗДАЕМ ТАБЛИЦЫ
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
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cafe_id INTEGER,
    title TEXT,
    price INTEGER,
    FOREIGN KEY (cafe_id) REFERENCES cafes (id)
)
''')

# 2. ТЕПЕРЬ ОЧИЩАЕМ СТАРЫЕ ДАННЫЕ (теперь таблицы точно существуют!)
cursor.execute('DELETE FROM menu')
cursor.execute('DELETE FROM cafes')

# 3. СБРАСЫВАЕМ СЧЕТЧИКИ ID ДО 1
cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'cafes'")
cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'menu'")

# 4. ВСТАВЛЯЕМ ТЕСТОВОЕ КАФЕ
cursor.execute(
    "INSERT INTO cafes (name, address, lat, lon) VALUES (?, ?, ?, ?)",
    ('Walter Cevapi', 'Stranhinjica Bana 57, Beograd', 44.8194, 20.4638)
)

conn.commit()


# главная страница
@app.get("/")
def home():
    return {"message": "Добро пожаловать в API Где Плескавица! Сервер работает."}

# Новое окно: выдаем список кафан из бд в браузер
@app.post("/cafes")
def create_cafe(cafe: CafeCreate):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()
    
    # Записываем новое кафе в базу вместе с его координатами
    local_cursor.execute(
        "INSERT INTO cafes (name, address, lat, lon) VALUES (?, ?, ?, ?)",
        (cafe.name, cafe.address, cafe.lat, cafe.lon)
    )
    local_conn.commit()
    local_conn.close()
    
    return {"status": "success", "message": f"Кафе '{cafe.name}' успешно добавлено с координатами!"}
    
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