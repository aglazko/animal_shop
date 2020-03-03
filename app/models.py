"""This module declares models(AnimalCenter, AccessRequest, Animal, Species) for database."""
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.interfaces import IAnimalCenter, IAccessRequest, ISpecies, IAnimal


class AnimalCenter(db.Model, IAnimalCenter):
    """
    This is a class for creating animalcenter table in database.
    It contains detailed information about each animal center.
    Attributes:
        id (int): Auto-generated id for user, primary key.
        login (string): Login(user name) that user use for authorization.
        password_hash (string): Store password in db insecure, so we keep only hash of password in db.
        address (string): The address of animal center.
    """
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))
    address = db.Column(db.String(200))
    # animals = db.relationship("Animal", backref="animals")

    def set_password(self, password):
        """
        Function that creates password hash.
        :param password: Password that set user.
        :return : None
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password, user_id=None):
        """
        The function that check user password when he/she is trying to authorize.
        :param password: Password that set user.
        :return True: If password is correct.
        :return False: If password is incorrect.
        """
        return check_password_hash(self.password_hash, password)

    def deserialize(self, record=None, long=False):
        """
        Function that create dictionary from object.
        :param long: Value of this param define which version of data will be returned. If value True function will
                     return long version of dictionary with such keys: id, login, address. Otherwise dictionary wil
                     not contain kye address.
        :return data: Dictionary with information about object.
        """
        data = {'id': self.id,
                'login': self.login}
                # TODO 'animals': self.animals}
        if long:
            data.update({'address': self.address})
        return data

    def get_centers(self):
        # records = []
        return [AnimalCenter.deserialize(record, long=False) for record in AnimalCenter().query.all()]

    def get_center_inform(self, id):
        record = AnimalCenter().query.get(id)
        return AnimalCenter.deserialize(record, long=True) if record else None

    def get_center_by_login(self, user_login):
        # record = AnimalCenter().query.filter_by(login=user_login).first()
        return AnimalCenter().query.filter_by(login=user_login).first()


class AccessRequest(db.Model, IAccessRequest):
    """
    Class for creating accessrequest table in db.
    In db will saved history of all successful requests.
    Parameters:
        id (int): Id of access request, auto-generated, primary key.
        center_id: Id of user that had access request.
        timestamp: Time when was request.
    """
    id = db.Column(db.Integer, primary_key=True)
    center_id = db.Column(db.Integer, db.ForeignKey("animal_center.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """
        Function that create dictionary from object.
        :return: Dictionary with information about object.
        """
        return {'id': self.id,
                'center_id': self.center_id,
                'timestamp': self.timestamp}

    def create_access_request(self, user_id):
        access_request = AccessRequest(center_id = user_id)
        db.session.add(access_request)
        db.session.commit()


class Animal(db.Model, IAnimal):
    """
    Class for creating animal table in db.
    It contains detailed information about each animal.
    Parameters:
        id (int): Id of animal, auto-generated, primary key.
        center_id (int): Animal owner id, foreign key.
        name (string): Animal name.
        description (string): Description of animal.
        age (int): Animal age.
        species_id (int): Species id to which belongs animal.
        price (float): Animal price.

    """
    id = db.Column(db.Integer, primary_key=True)
    center_id = db.Column(db.Integer, db.ForeignKey("animal_center.id"))
    name = db.Column(db.String(40))
    description = db.Column(db.String(500), nullable=True)
    age = db.Column(db.Integer)
    species_id = db.Column(db.Integer, db.ForeignKey("species.id"))
    price = db.Column(db.Float, nullable=True)

    def deserialize(self, record=None, long=False):
        """
        Function that create dictionary from object.
        :param long: Value of this param define which version of data will be returned. If value True function will
                     return long version of dictionary with such keys: id, name, center_id, description, age,
                     species_id, price. Otherwise dictionary wil contain only id and name.
        :return data: Dictionary with information about object.
        """
        data = {'id': self.id,
                'name': self.name}
        if long:
            data.update({
                'center_id': self.center_id,
                'description': self.description,
                'age': self.age,
                'species_id': self.species_id,
                'price': self.price
            })
        return data

    def get_animals(self):
        animals = [animal.deserialize() for animal in Animal().query.all()]
        return animals

    def add_animal(self, data, userid):
        animal = Animal(name=data['name'], center_id=userid,
                               description=data['description'], price=data['price'],
                               species_id=data['species_id'], age=data['age'])
        db.session.add(animal)
        db.session.commit()
        return animal.deserialize(animal)

    def get_animal(self, animal_id):
        animal = Animal().query.get(animal_id)
        return animal.deserialize(long=True)

    def delete_animal(self, animal_id):
        animal = Animal().query.get(animal_id)
        db.session.delete(animal)
        db.session.commit()

    def update_animal(self, animal=None, data_upd=None, animal_id=None):
        animal = Animal().query.get(animal_id)
        for key, value in data_upd.items():
            setattr(animal, key, value)
        db.session.commit()


class Species(db.Model, ISpecies):
    """
    Class for creating species table in db.
    Contains detailed information about species.
    Parameters:
        id (int): Species id.
        name (string): Species name.
        description (string): Description of species.
        price (float): Species price.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(500), nullable=True)
    price = db.Column(db.Float, nullable=True)

    def deserialize(self, record=None, long=False):
        """
        Function that create dictionary from object.
        :return: Dictionary with information about object.
        """
        if long:
            data = {'id': self.id,
                    'name': self.name,
                    'description': self.description,
                    'price': self.price}
        return data

    def get_species(self):
        result = db.session.query(
            Species.name, db.func.count(Animal.name)) \
            .join(Animal, Species.id == Animal.species_id, isouter=True) \
            .group_by(Species.id).all()
        return [{'species_name': name, 'count_of_animals': count} for name, count in result]

    def get_species_inform(self, id):
        species = Species().query.get(id)
        animals = Animal().query.filter_by(species_id=id).all()
        if species:
            return species.deserialize(long=True),[animal.deserialize(long=True) for animal in animals]
        else:
            return None

