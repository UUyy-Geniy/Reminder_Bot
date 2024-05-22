import os
import logging
import subprocess  # Импорт модуля subprocess
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

class Database:
    def __init__(self, db_url):
        self.session_maker = None
        self.url = db_url
        self.engine = None

    def connect(self):
        try:
            self.engine = create_engine(self.url)
            self.session_maker = sessionmaker(bind=self.engine)
            self.sql_query(query=select(1))
            logging.info("Database connected")
            self.run_migrations() # Вызов метода для запуска миграций
        except Exception as e:
            logging.error(e)
            logging.error("Database didn't connect")

    def run_migrations(self):
        # Функция для запуска Alembic миграций
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            logging.info("Migrations applied successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to apply migrations: {e}")

    def sql_query(self, query, is_single=True, is_update=False, is_delete=False):
        with self.session_maker(expire_on_commit=True) as session:
            response = session.execute(query)
            if is_delete or is_update:
                session.commit()
            if not is_update and not is_delete:
                return response.scalars().first() if is_single else response.all()

    def create_object(self, model, ):
        with self.session_maker(expire_on_commit=True) as session:
            session.add(model)
            session.commit()
            session.refresh(model)
            return model.id

    def create_objects(self, model_s: []):
        with self.session_maker(expire_on_commit=True) as session:
            session.add_all(model_s)
            session.commit()

load_dotenv()
logging.basicConfig(level=logging.INFO)
db = Database(os.getenv("DB_URL"))
db.connect()