from pydantic import BaseModel, Field
from typing import Optional


class ExternalVinylViewSchema(BaseModel):
    title: str = Field(..., description="Título do álbum/lançamento")
    year: Optional[int] = Field(None, description="Ano de lançamento")
    genre: Optional[str] = Field(None, description="Gêneros musicais")
    cover_image: Optional[str] = Field(None, description="URL da capa do disco")

class ListExternalVinylSchema(BaseModel):
    results: list[ExternalVinylViewSchema]