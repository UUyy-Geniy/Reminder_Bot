# import logging
#
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
#
#
# class Database:
#     def __init__(self, db_url: str):
#         self.db_url = db_url
#         self.__engine = None
#
#     async def create_object(self, model, **attributes):
#         async with AsyncSession(self.__engine, expire_on_commit=False) as session:
#             object = model(**attributes)
#             session.add(object)
#             await session.commit()
#             return object
#
#     async def sql_query(self, query, single=True, is_update=False, *args, **kwargs):
#         async with AsyncSession(self.__engine) as session:
#             result = await session.execute(query)
#             if not is_update:
#                 return result.scalars().first() if single else result.scalars().all()
#             await session.commit()
#             return result
#
#     async def connect(self):
#         self.__engine = create_async_engine(self.db_url)
#         await self.sql_query(query=select(1))
#         logging.info("Database has been connected")
#
#     async def disconnect(self):
#         if self.__engine:
#             await self.__engine.dispose()
#         logging.info("Database has been disconnected")


import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select, update, delete, Engine, literal_column, join
from sqlalchemy.orm import sessionmaker
from bd import models


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
        except Exception as e:
            logging.error(e)
            logging.error("Database didn't connect")

    def sql_query(self, query, is_single=True, is_update=False):
        with self.session_maker(expire_on_commit=True) as session:
            response = session.execute(query)
            if not is_update:
                return response.scalars().first() if is_single else response.all()
            session.commit()

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


# remove_user('Ivan')
#db.create_object(model=models.User(name="ams"))
# print([user.name for user in sql_query(query=select(models.User), is_single=False)])
# sql_query(query=update(models.User).where(models.User.name == "ilsaf").values(name="fedya"), is_update=True)