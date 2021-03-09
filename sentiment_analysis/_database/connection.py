from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

class DBConnection:
    """
    A SQLAlchemy database connection manager to manage sessions
    and provide context management.
    """
    
    def __init__(self, connection_url):
        self.connection_url = connection_url
        self.engine = create_engine(self.connection_url)
        self.Session = sessionmaker(bind=self.engine)

    def __enter__(self):
        self.session = self.Session()
        return self.session
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.session.commit()
        self.session.close()