"""Classes to retrieve data from database via SQL"""

from app import db
from copy import copy
from werkzeug.security import check_password_hash
from app.interfaces import IAnimalCenter, IAccessRequest, ISpecies, IAnimal
from datetime import datetime


class AnimalsDAO(IAnimal):
    # @staticmethod
    def deserialize(self, record=None, long=False):
        data = {
            'id': record[0],
            'name': record[2]
        }
        if long:
            data.update({
                'center_id': record[1],
                'description': record[3],
                'age': record[4],
                'species_id': record[5],
                'price': record[6]
            })
        return data

    # @staticmethod
    def get_animals(self):
        records = db.engine.execute("SELECT * FROM animal;")
        return [AnimalsDAO().deserialize(record) for record in records]

    # @staticmethod
    def get_animal(self, animal_id):
        record = db.engine.execute(
            "SELECT * FROM animal WHERE id={}".format(animal_id)).first()
        return AnimalsDAO().deserialize(record, long=True) if record else None

    # @staticmethod
    def delete_animal(self, animal_id):
        db.engine.execute("DELETE FROM animal WHERE id={}".format(animal_id))

    # @staticmethod
    def update_animal(self, animal=None, data_upd=None, animal_id=None):
        animal = copy(animal)
        animal_id = animal.pop('id')
        update_string = ','.join(
            ["{}='{}'".format(key, value) for key, value in animal.items()])
        db.engine.execute(
            "UPDATE animal SET {} WHERE id={}".format(
                update_string, animal_id))

    def add_animal(self, data, userid):
        db.engine.execute("INSERT INTO animal (name, center_id, description, price, species_id, age) "
                          "VALUES ('{}', {}, '{}', {}, {}, {});".format(data['name'], userid, data['description'],
                                                                        data['price'], data['species_id'], data['age']))
        animal = db.engine.execute("SELECT * FROM animal WHERE id = (SELECT MAX(id) FROM animal);").first()
        return AnimalsDAO().deserialize(animal)


class AnimalCentersDAO(IAnimalCenter):
    # @staticmethod
    def deserialize(self, record=None, long=False):
        data = {'id': record.id,
                'login': record.login}
        if long:
            data.update({'address': record.address})
        return data

    # @staticmethod
    def get_centers(self):
        records = db.engine.execute("SELECT * FROM animal_center;")
        return [AnimalCentersDAO().deserialize(record, long=False) for record in records]

    # @staticmethod
    def get_center_inform(self, id):
        record = db.engine.execute(
            "SELECT * FROM animal_center WHERE id={};".format(id)).first()
        animals = db.engine.execute(
            "SELECT * FROM animal WHERE center_id={};".format(id)
        )
        if record:
            return AnimalCentersDAO().deserialize(record, long=True), [AnimalsDAO().deserialize(animal) for animal in animals] if record else None
        else:
            return None

    # @staticmethod
    def get_center_by_login(self, user_login):
        record = db.engine.execute(
            "SELECT * FROM animal_center WHERE login='{}';".format(user_login)).first()
        return AnimalCentersDAO().deserialize(record, long=True) if record else None

    # @staticmethod
    def check_password(self, password, user_id=None):
        record = db.engine.execute(
            "SELECT password_hash FROM animal_center "
            "WHERE id ={};".format(user_id)).first()
        return check_password_hash(record.password_hash, password)


class AccessRequestDAO(IAccessRequest):
    # @staticmethod
    def create_access_request(self, user_id):
        db.engine.execute(
            "INSERT INTO access_request (center_id, timestamp) VALUES ({}, '{}');".format(user_id, datetime.now()))
#         TODO set time


class SpeciesDAO(ISpecies):
    # @staticmethod
    def deserialize(self, record=None, long=False):
        data = {'species_name': record[0],
                'count_of_animals': record[1]}
        if long:
            data = {'id': record[0],
                'name': record[1],
                'description': record[2],
                'price': record[3]}
        return data

    # @staticmethod
    def get_species(self):
        records = db.engine.execute("SELECT species.name, count(animal.name) FROM species "
                                   "LEFT OUTER JOIN animal ON species.id = animal.species_id "
                                   "GROUP BY species.name")
        return [SpeciesDAO().deserialize(record) for record in records]

    # @staticmethod
    def get_species_inform(self, id):
        record = db.engine.execute("SELECT * FROM species WHERE id = {};". format(id)).first()
        animals = db.engine.execute("SELECT * FROM animal WHERE species_id = {};".format(id))
        if record:
            return SpeciesDAO().deserialize(record, long=True),[AnimalsDAO().deserialize(animal) for animal in animals]
        else:
            return None

    def add_species(self, data):
        db.engine.execute("INSERT INTO species (name, description, price) "
                          "VALUES ('{}', '{}', {});".format(data['name'],
                                                    data['description'], data['price']))
        specie = db.engine.execute("SELECT * FROM species WHERE id = (SELECT MAX(id) FROM species);").first()
        return SpeciesDAO().deserialize(specie, long=True)