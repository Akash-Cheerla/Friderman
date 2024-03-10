from typing import List

from fastapi import Query
from pydantic import BaseModel, Field


class PossibleVariantsRequest(BaseModel):
    possiblevariants: List[str] = Field(Query(...))
