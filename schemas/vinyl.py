from pydantic import BaseModel
from typing import List, Optional, Literal
from model.vinyl import Vinyl

GenreLiteral = Literal[
    "Rock",
    "Pop",
    "Jazz",
    "Electronic",
    "Classical",
    "Hip Hop",
    "Metal",
    "Outro"
]

ConservationStateLiteral = Literal[
    "Novo (M)",
    "Excelente (NM)",
    "Muito Bom (VG+)",
    "Bom (VG)",
    "Regular (G)"
]

class VinylSchema(BaseModel):
    name: str
    genre: Optional[GenreLiteral] = None
    year: int
    artist: str
    conservation_state: ConservationStateLiteral

    class Config:
        orm_mode = True


def present_vinyl(vinyl: Vinyl):
    """Returns a JSON representation of one vinyl following VinylViewSchema."""
    return {
        "id": vinyl.id,
        "name": vinyl.name,
        "genre": vinyl.genre,
        "year": vinyl.year,
        "artist": vinyl.artist,
        "conservation_state": vinyl.conservation_state,
        "created_datetime": vinyl.created_datetime.isoformat() if vinyl.created_datetime else None
    }


def present_vinyls(vinyls: List[Vinyl]):
    """
    Returns a JSON representation of multiple vinyls
    following the ListVinylsSchema structure.
    """
    result = []
    for vinyl in vinyls:
        result.append({
            "id": vinyl.id,
            "name": vinyl.name,
            "genre": vinyl.genre,
            "year": vinyl.year,
            "artist": vinyl.artist,
            "conservation_state": vinyl.conservation_state,
            "created_datetime": vinyl.created_datetime.isoformat() if vinyl.created_datetime else None
        })
    return {"vinyls": result}


class VinylSearchSchema(BaseModel):
    """Schema for searching a vinyl by name or artist."""
    name: str


class ListVinylsSchema(BaseModel):
    """Schema that represents a list of vinyls returned by the API."""
    vinyls: List[VinylSchema]


class VinylViewSchema(BaseModel):
    """Schema defining how an individual vinyl is returned."""
    id: int
    name: str
    genre: Optional[str]
    year: int
    artist: str
    conservation_state: str
    created_datetime: Optional[str]


class VinylUpdateSchema(BaseModel):
    id: int
    name: str
    genre: Optional[GenreLiteral]
    year: int
    artist: str
    conservation_state: ConservationStateLiteral


class VinylPath(BaseModel):
    id: int
    
class VinylDeleteSchema(BaseModel):
    """Schema representing the successful deletion of a vinyl."""
    mesg: str
    id: int