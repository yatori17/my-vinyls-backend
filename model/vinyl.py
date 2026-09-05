from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from typing import Union

from model import Base

class Vinyl(Base):
    __tablename__ = 'vinyl'

    id = Column(Integer, primary_key=True)
    name = Column(String(140), nullable=False)
    genre = Column(String(140))
    year = Column(Integer, nullable=False)
    artist = Column(String(140), nullable=False)
    conservation_state = Column(String(140), nullable=False)
    created_datetime = Column(DateTime, default=datetime.now)
    
    def __init__(self, name: str, genre: str, year: int,
                 artist: str, conservation_state: str, 
                 created_datetime: Union[datetime, None] = None):
        """
        Create a Vinyl

        Arguments:
            name: Vinyl name / title;
            genre: Vinyl genre;
            year: Release year;
            artist: Artist name;
            conservation_state: Conservation state;
            created_datetime: Created Datetime;
        """
        self.name = name
        self.genre = genre
        self.year = year
        self.artist = artist
        self.conservation_state = conservation_state
        if created_datetime:
            self.created_datetime = created_datetime