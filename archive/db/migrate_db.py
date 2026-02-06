from sqlalchemy import Column, Text, text, Inspector

from db.session import engine


import logging

logger = logging.getLogger("app")

async def add_column(engine, table_name, column):
    column_name = column.compile(dialect=engine.dialect)
    column_type = column.type.compile(engine.dialect)
    with engine.connect() as connection:
        connection.execute(text(f'ALTER TABLE {table_name} ADD COLUMN  {column_name} {column_type};'))

async def migrate():
    new_column = Column('parameters', Text)
    table_name= "solutionrouting"
    inspector = Inspector.from_engine(engine)
    if new_column.name not in [col['name'] for col in inspector.get_columns(table_name)]:
        await add_column(engine, table_name, new_column)





