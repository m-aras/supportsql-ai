from fastapi import FastAPI
from pydantic import BaseModel
from ollama import chat
from sqlalchemy import text
from db import engine
from sql_guard import validate_sql

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"message": "SQL Support AI is running"}


@app.get("/films")
def get_films():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT film_id, title, release_year
                FROM film
                LIMIT 10
            """)
        )

        films = []

        for row in result:
            films.append({
                "film_id": row.film_id,
                "title": row.title,
                "release_year": row.release_year
            })

        return films


@app.post("/ask")
def ask_database(request: ChatRequest):

    prompt = f"""
You are a PostgreSQL SQL assistant.

Database tables available:

film(
    film_id,
    title,
    description,
    release_year,
    rental_rate,
    length,
    replacement_cost
)

inventory(
    inventory_id,
    film_id,
    store_id
)

rental(
    rental_id,
    rental_date,
    inventory_id,
    customer_id,
    return_date,
    staff_id
)

payment(
    payment_id,
    customer_id,
    staff_id,
    rental_id,
    amount,
    payment_date
)

Convert the user's question into PostgreSQL SQL.

Rules:
- Only SELECT queries.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER or CREATE.
- Return only SQL.
- Do not explain anything.


Question:
{request.message}
"""

    response = chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        think=False
    )

    sql_query = (response.message.content or "").strip()

    # Qwen düşünme çıktısı verdiyse sadece sonrasını al
    if "</think>" in sql_query:
        sql_query = sql_query.split("</think>")[-1]
    # Markdown SQL bloklarını temizl
    sql_query = sql_query.replace("```sql", "")
    sql_query = sql_query.replace("```", "")
    sql_query = sql_query.strip()

    # sqlglot ile AST tabanlı doğrulama 
    is_safe, error_message = validate_sql(sql_query)
    if not is_safe:
        return {
            "error": error_message,
            "generated_sql": sql_query
        }

    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))

            rows = []

            for row in result:
                rows.append(dict(row._mapping))

        return {
            "question": request.message,
            "sql": sql_query,
            "result": rows
        }
    except Exception as e:
        return {
            "error": "Sorgu çalıştırılamadı.",
            "generated_sql": sql_query
        }