from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)

    favorities: Mapped[list['Favorite']] = relationship(back_populates="user")

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "password": self.password,
            "is_active": self.is_active,
            # do not serialize the password, its a security breach
        }

    @classmethod
    def create_user(cls, data):
        try:
            new_user = {**data}
            db.session.add(new_user)
            db.session.commit()
            return True
        except Exception as error:
            print(error)
            return False

class Character(db.Model):

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    gender: Mapped[str] = mapped_column(String)
    hair_color: Mapped[str] = mapped_column(String)
    eye_color: Mapped[str] = mapped_column(String)

class Planet(db.Model):

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    climate: Mapped[str] = mapped_column(String)
    population: Mapped[int] = mapped_column(Integer)
    orbital_period: Mapped[int] = mapped_column(Integer)
    rotation_period: Mapped[int] = mapped_column(Integer)
    diameter: Mapped[int] = mapped_column(Integer)

class Vehicle(db.Model):

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    cargo_capacity: Mapped[int] = mapped_column(Integer)
    consumables: Mapped[str] = mapped_column(String)
    cost_in_credits: Mapped[int] = mapped_column(Integer)

class Favorite(db.Model):

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    model: Mapped[str] = mapped_column(String(50))
    model_id: Mapped[int] = mapped_column(Integer)

    user: Mapped['User'] = relationship(back_populates="favorities")

    def get_item(self):
        if self.model == "character":
            return db.session.get(Character, self.model_id)
        elif self.model == "planet":
            return db.session.get(Planet, self.model_id)
        elif self.model == "vehicle":
            return db.session.get(Planet, self.model_id)