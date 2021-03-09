from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# base class for models
Base = declarative_base()


class Companies(Base):
    __tablename__ = 'companies'
    __table_args__ = {'extend_existing': True} 
    
    id = Column(
        Integer,
        Sequence('companies_id_seq'), 
        primary_key=True,
        autoincrement='auto'
    )
    cik = Column(
        Integer,
        nullable=False
    )
    ticker = Column(
        String(16),
        unique=True,
        nullable=False
    )
    title = Column(
        String(320),
        nullable=False
    )
    
    def __repr__(self):
         return f"<company(id=%s, <cik(cik=%s, ticker=%s, title=%s)>" % \
             (self.id, self.cik, self.ticker, self.title)
             

class Platforms(Base):
    __tablename__ = 'platforms'
    __table_args__ = {'extend_existing': True} 
    
    id = Column(
        Integer, 
        Sequence('platforms_id_seq'), 
        primary_key=True,
        autoincrement='auto'
    )
    name = Column(
        String(32),
        unique=True,
        nullable=False
    )
    url = Column(Text)
    
    def __repr__(self):
        return f"<platform(id=%s, name=%s, url=%s)>" % \
            (self.id, self.name, self.url)


class CompanySentiment(Base):
    __tablename__ = 'company_sentiment'
    __table_args__ = {'extend_existing': True} 
    
    # columns
    id = Column(
        Integer, 
        Sequence('company_sentiment_id_seq'), 
        primary_key=True,
        autoincrement='auto'
    )
    company_id = Column(
        Integer,
        ForeignKey('companies.id'),
        nullable=False
    )
    platform_id = Column(
        Integer,
        ForeignKey('platforms.id'),
        nullable=False
    )
    sentiment_score = Column(Integer)

    # relationships
    company = relationship('Companies', backref='companies')
    platform = relationship('Platforms', backref='platforms')
    
    def __repr__(self):
        return f"<sentiment(id= %s, <company_id(name=%s, platform_id=%s, sentiment_score=%s)>" % \
            (self.id, self.company_id, self.platform_id, self.sentiment_score)


class Subreddits(Base):
    __tablename__ = 'subreddits'
    __table_args__ = {'extend_existing': True} 
    
    id = Column(
        Integer,
        Sequence('subreddits_id_seq'),
        primary_key=True,
        autoincrement='auto'
    )
    name = Column(
        String(32),
        nullable=False
    )
    subreddit_id = Column(
        String(32),
        unique=True,
        nullable=False
    )
    subscribers = Column(Integer)
    
    def __repr__(self):
        return f"<subreddit(id=%s, name=%s, subreddit_id=%s, subscribers=%s)>" % \
            (self.id, self.name, self.subreddit_id, self.subscribers)
    

class RedditComments(Base):
    __tablename__ = 'reddit_comments'
    __table_args__ = {'extend_existing': True} 
    
    id = Column(
        Integer,
        Sequence('reddit_comments_id_seq'),
        primary_key=True,
        autoincrement='auto'
    )
    submission_id = Column(
        String(32),
        ForeignKey('reddit_submissions.submission_id'),
        nullable=False,
    )
    comment_id = Column(
        String(32),
        unique=True,
        nullable=False
    )
    created_utc = Column(
        DateTime(timezone=True),
        nullable=False
    )
    cleaned_comment = Column(Text)
    score = Column(Integer)
    
    def __repr__(self):
        return f"<comment(id=%s, submission_id=%s, comment_id=%s, created_utc=%s, cleaned_comment=%s, score=%s)>" % \
            (self.id, self.submission_id, self.comment_id, self.created_uct, self.cleaned_comment, self.score)


class RedditSubmissions(Base):
    __tablename__ = 'reddit_submissions'
    __table_args__ = {'extend_existing': True} 
    
    id = Column(
        Integer,
        Sequence('reddit_submissions_id_seq'),
        primary_key=True,
        autoincrement='auto'
    )
    ticker = Column(
        String(16),
        ForeignKey('companies.ticker'),
        nullable=False
    )
    subreddit_id = Column(
        String(32),
        ForeignKey('subreddits.subreddit_id'),
        nullable=False
    )
    submission_id = Column(
        String(32),
        unique=True,
        nullable=False
    )
    created_utc = Column(
        DateTime(timezone=True),
        nullable=False
    )
    title = Column(Text)
    score = Column(Integer)
    
    def __repr__(self):
        return f"<reddit_submission(id=%s, ticker=%s, subreddit_id=%s, submission_id=%s, created_utc=%s, url=%s, title=%s, score=%s)>" % \
            (self.id, self.ticker, self.subreddit_id, self.submission_id, self.created_utc, self.url, self.title, self.score)