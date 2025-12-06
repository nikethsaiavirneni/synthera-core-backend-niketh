from sqlalchemy import text
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil

engine = get_engine()
db_util = DBSessionUtil(engine)

with engine.connect() as connection:
    connection.execute(text("ALTER TABLE meeting ADD PRIMARY KEY (meeting_title);"))