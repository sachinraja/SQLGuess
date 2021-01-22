import os
import json
import random
import threading
from typing import Tuple, List
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from app.game_models import Base, Animal, State, Location, AnimalLocation

class GameDatabase():
    def __init__(self):
        # sqlalchemy: create initial engine with file db
        load_dotenv()
        self.engine = create_engine(os.environ['DATABASE_URL'])
        self.Session = sessionmaker(self.engine) # pylint: disable=invalid-name

        # get lengths of tables for random fetching later on
        with open('seed_data/location.json', 'r') as f:
            locations = json.load(f)['locations']

        self.locations_length = len(locations)

        # if the schema 'game' does not exist, create the schema and its basic layout
        if not self.engine.dialect.has_schema(self.engine, 'game'):
            self.engine.execute(CreateSchema('game'))

            # allow readonly user to access schema
            self.engine.execute("GRANT USAGE ON SCHEMA game TO readonly;")

            # create tables in schema
            Base.metadata.create_all(self.engine)

            # allow readonly user to access all tables in schema after they are created
            self.engine.execute("GRANT SELECT ON ALL TABLES IN SCHEMA game TO readonly;")

            self.load_seed_data()

        self._readonly_conn = psycopg2.connect(os.environ['READONLY_DATABASE_URL'])

    def execute_user_input(self, query : str) -> dict:
        """Execute a query from user input.

        Args:
            query (str): The query input from the user.

        Returns:
            dict: The result of cur.fetchall() after the query; the results of the query.
        """

        returning = {}

        with self._readonly_conn.cursor() as cur:
            # attempt to execute query, ready to catch error if user input is bad
            query_timeout = threading.Timer(0.5, self._readonly_conn.cancel)
            query_timeout.start()
            try:
                cur.execute(query)
                returning['result'] = list(cur.fetchall())
                returning['columns'] = [desc[0] for desc in cur.description]
            except Exception as e: # pylint: disable=broad-except
                if isinstance(e, psycopg2.errors.QueryCanceled): # pylint: disable=no-member
                    returning['error'] = "canceling statement due to statement timeout: execution was longer than 0.5 seconds"

                else:
                    returning['error'] = str(e)

            query_timeout.cancel()
            self._readonly_conn.rollback()
            return returning

    def get_random_location(self) -> Tuple[Location, List[Tuple]]:
        """Get a random location and a list of hints.

        Returns:
            Tuple[Location, List[Tuple]]: The random location and a list of hints for it.
        """

        random_location_id = random.randint(1, self.locations_length)

        session = self.Session()
        location = session.query(Location).filter(Location.id == random_location_id).one()
        state_name = session.query(State).filter(State.id == location.state_id).one().name

        hints = [("biome", location.biome), ("state name", state_name)]
        for animal_location in session.query(AnimalLocation).filter(AnimalLocation.location_id == location.id).all():
            animal = session.query(Animal).filter(Animal.id == animal_location.animal_id).one()
            hints.append(("one animal's name", animal.name))

        session.close()

        return location, hints

    def load_seed_data(self) -> None:
        """Create seed data for the tables."""

        with open('seed_data/location.json', 'r') as f:
            locations_data = json.load(f)['locations']

            session = self.Session()
            for location in locations_data:
                state_name = location["state"]

                state = session.query(State).filter(State.name == state_name).scalar()

                if not state:
                    state = State(name=state_name)
                    session.add(state)
                    session.commit()
                    session.refresh(state)

                insert_location = Location(name=location["name"], biome=location["biome"], state_id=state.id)
                session.add(insert_location)
                session.commit()
                session.refresh(insert_location)

                for animal_name in location["animals"]:
                    animal = session.query(Animal).filter(Animal.name == animal_name).scalar()

                    if not animal:
                        animal = Animal(name=animal_name)
                        session.add(animal)
                        session.commit()
                        session.refresh(animal)

                    session.add(AnimalLocation(location_id=insert_location.id, animal_id=animal.id))

        # commit anything left (last location's rows)
        session.commit()