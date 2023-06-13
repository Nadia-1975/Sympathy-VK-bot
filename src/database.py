import sqlalchemy as sq
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# классы пользователя, предложенных пользователей, списка избранных и списка отсеянных
class User(Base):
    __tablename__ = 'user'

    user_id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, unique=True)

    def __str__(self):
        return f'User {self.id}: {self.user_id}'


class UserOfferData(Base):
    __tablename__ = 'user_offers'

    user_id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, unique=True)

    def __str__(self):
        return f'User_offers {self.id}: {self.user_id}'


class WhiteList(Base):
    __tablename__ = 'white_list'

    user_id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String, nullable=False)
    last_name = sq.Column(sq.String, nullable=False)
    vk_link = sq.Column(sq.String, unique=True, nullable=False)

    def __str__(self):
        return f'White_list {self.id}: {self.user_id}, {self.first_name},' \
               f'{self.last_name}, {self.vk_link}'


class BlackList(Base):
    __tablename__ = 'black_list'

    user_id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, unique=True)

    def __str__(self):
        return f'Black_list {self.id}: {self.user_id}'


# автоматическое создание всех таблиц
def create_tables(engine):
    Base.metadata.create_all(engine)


# автоматическая очистка всех таблиц (по завершении работы бота)
def drop_tables(engine):
    Base.metadata.drop_all(engine)
