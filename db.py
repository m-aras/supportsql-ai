from sqlalchemy import create_engine

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "dvdrental"
DB_USER = "postgres"
DB_PASSWORD = "1234"

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)