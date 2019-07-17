from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Catalog, Base, CatalogItem,User

engine = create_engine('sqlite:///catalogitem.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

catalog1=Catalog(user_id=1,name="Soccer")
session.add(catalog1)
session.commit()

catalog2=Catalog(user_id=1,name="BasketBall")
session.add(catalog2)
session.commit()

catalog3=Catalog(user_id=1,name="Baseball")
session.add(catalog3)
session.commit()

catalog4=Catalog(user_id=1,name="Frisbee")
session.add(catalog4)
session.commit()

catalog5=Catalog(user_id=1,name="Snowboarding")
session.add(catalog5)
session.commit()

catalog6=Catalog(user_id=1,name="Rock Climbing")
session.add(catalog6)
session.commit()

catalog7=Catalog(user_id=1,name="Foosball")
session.add(catalog7)
session.commit()

catalog8=Catalog(user_id=1,name="Skating")
session.add(catalog8)
session.commit()

catalog9=Catalog(user_id=1,name="Hockey")
session.add(catalog9)
session.commit()

print("Catalog records added!!")
