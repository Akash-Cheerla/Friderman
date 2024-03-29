from typing import List, Union

from fastapi import Query
from pydantic import BaseModel, Field


class SingleItem(BaseModel):
    item: str
    quantity: int
    variantflag: bool
    possiblevariants: List[str]
    message: str


class MatchedSingleItem(BaseModel):
    item: str
    quantity: int
    variantflag: bool
    matched_variant: str
    message: str
    special_instruction: bool


class ConfirmedSingleItem(BaseModel):
    item: str
    quantity: int
    variantflag: bool
    matched_variant: str
    message: str
    special_instruction: str


class TextFirstStepRequest(BaseModel):
    restaurant_id:  int
    text: str
    items: List[SingleItem]


class TextSelectVariantRequest(BaseModel):
    restaurant_id: int
    text: str
    items: List[Union[SingleItem, MatchedSingleItem]]


class TextSpecialInstructionRequest(BaseModel):
    restaurant_id: int
    text: str
    items: List[Union[SingleItem, MatchedSingleItem, ConfirmedSingleItem]]


class TextConfirmOrderRequest(BaseModel):
    restaurant_id: int
    text: str
    items: List[ConfirmedSingleItem]


class PossibleVariantsRequest(BaseModel):
    possiblevariants: List[str] = Field(Query(...))
