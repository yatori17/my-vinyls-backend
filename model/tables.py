from sqlalchemy import Table, Column, Integer, ForeignKey, String
from model import Base

music_artist = Table(
    "music_artist",
    Base.metadata,
    Column("music_id", Integer, ForeignKey("music.id"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artist.pk_artist"), primary_key=True))