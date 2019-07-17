from sqlalchemy import Column,ForeignKey,Integer,String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base= declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Catalog(Base):
    __tablename__='catalog'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer,ForeignKey('user.id'))
    user=relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }

class CatalogItem(Base):
    __tablename__='catalog_item'
    title=Column(String(80),nullable=False)
    id=Column(Integer, primary_key = True)
    description = Column(String(250))
    catalog_id=Column(Integer,ForeignKey('catalog.id'))
    catalog=relationship(Catalog,backref='catalog_items')
    user_id = Column(Integer,ForeignKey('user.id'))
    user=relationship(User)



    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'description'         : self.description,
           'title'         : self.title,
           'id'         : self.id,

       }

engine = create_engine('sqlite:///catalogitem.db')
Base.metadata.create_all(engine)