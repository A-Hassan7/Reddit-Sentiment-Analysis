import pandas as pd
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker

from config import DatabaseConfig, Loggers

from . import models
from .connection import DBConnection

# database connection url
DBURL = URL(
    drivername=DatabaseConfig.DATABASE_DRIVER_NAME,
    database=DatabaseConfig.DATABASE_NAME
)


class DatabaseManager:
    """
    The DataBaseManager class provides methods to query and insert
    values into a database. Database configurations can be provided
    in the .env file.

    This class is built on top of SQLAlchemy an ORM for python
    https://www.sqlalchemy.org/
    """

    def __init__(self):

        self.logger = Loggers.console

        # Gateway to database session
        self.Connection = DBConnection(DBURL)

        # Map models to database tables
        self._map_models()

        # configure sqlite
        if DBURL.drivername == 'sqlite':
            self._configure_sqlite()

    def insert_values(self, model, values):
        """Insert values into a database table

        Args:
            model (models.model): 
                An ORM model representing a table from database.models
            values (pd.DataFrame): Pandas dataframe of values to insert

        Raises:
            TypeError: If values passed are not instance of pandas.DataFrame
        """

        if isinstance(values, pd.DataFrame):
            # convert dataframe to row [{column: value, column: value}]
            values = values.to_dict(orient='records')
            
            with self.Connection as session:
                session.bulk_insert_mappings(
                    mapper=model,
                    mappings=values
                )
        else:
            raise TypeError('Values should be an instance of pandas.DataFrame')
        
    
    def update_values(self, model, values, on):
        """Update values in the database

        Args:
            model (models.model):
                An ORM model representing a table from database.models
            values (pd.DataFrame): Pandas dataframe of values to update
            on (str): column to match
        """
        
        original = self.get_values(model)
        merged = pd.merge(original, values, on=on)

        # Keep only updated and id columns
        ###### Refactor, bad implamentation
        for col in list(merged.columns):
            if col.endswith('_x'):
                merged.drop(col, axis=1, inplace=True)
            elif col.endswith('_y'):
                merged.rename(columns={col: col[:-2]}, inplace=True)
            else:
                if col != 'id':
                    merged.drop(col, axis=1, inplace=True)
        
        with self.Connection as session:
            session.bulk_update_mappings(
                mapper=model,
                mappings=merged.to_dict(orient='records')
            )
        
    def get_values(self, model, filters=None):
        #TODO: implament .filter for conditional querying
        
        filters = [] if not filters else filters
        with self.Connection as session:
            query = session.query(model).filter(*filters)
        
        values = pd.read_sql(
            sql=query.statement,
            con=self.Connection.engine,
        )
        
        return values
            
    def _map_models(self):
        """
        Map ORM models to database tables
        """
        models.Base.metadata.create_all(bind=self.Connection.engine)

    def _configure_sqlite(self):
        """
        Enforce foreign key constraints in sqlite
        """
        with self.Connection as session:
            session.execute('pragma foreign_keys=ON')


# dbm = DatabaseManager()

# data = pd.DataFrame({
#     'name': ['reddit', 'twitter', 'facebook'],
#     'url': ['www.reddit.co.uk', 'www.twitter.co.uk', 'www.facebook.co.uk']
# })

# # dbm.insert_values(models.Platforms, data)
# dbm.update_values(models.Platforms, data, on='name')