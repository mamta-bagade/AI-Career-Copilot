from sqlalchemy import Column, Integer, String, Text, ForeignKey
from db import Base
from werkzeug.security import generate_password_hash, check_password_hash

class User(Base):
    __tablename__="users"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(256))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Reports(Base):
    __tablename__= "reports"  

    id = Column(Integer, primary_key=True) 
    user_id = Column(Integer, ForeignKey("users.id"))
    resume_text = Column(Text)
    result = Column(Text)