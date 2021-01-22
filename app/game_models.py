from sqlalchemy import Column, Integer, String, Identity, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Animal(Base):
    __tablename__ = 'animal'
    __table_args__ = {'schema': 'game'}
    id = Column('animal_id', Integer, Identity(), primary_key=True)
    name = Column('animal_name', String(50), nullable=False)
    relationship('AnimalLocation')

class State(Base):
    __tablename__ = 'state'
    __table_args__ = {'schema' : 'game'}
    id = Column('state_id', Integer, Identity(), primary_key=True)
    name = Column('state_name', String(50), nullable=False)
    locations = relationship('Location')

class Location(Base):
    __tablename__ = 'location'
    __table_args__ = {'schema' : 'game'}
    id = Column('location_id', Integer, Identity(), primary_key=True)
    name = Column('location_name', String(50), nullable=False)
    biome = Column('location_biome', String(50), nullable=False)
    state_id = Column('state_id', Integer, ForeignKey(State.id))
    relationship('AnimalLocation')

class AnimalLocation(Base):
    __tablename__ = 'location_animals'
    __table_args__ = (
        PrimaryKeyConstraint('location_id', 'animal_id'),
        {'schema': 'game'}
        )

    location_id = Column('location_id', Integer, ForeignKey(Location.id))
    animal_id = Column('animal_id', Integer, ForeignKey(Animal.id))
