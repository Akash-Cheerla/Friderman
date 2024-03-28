import uuid

from loguru import logger
from fastapi import APIRouter, HTTPException

from models import (
    TextFirstStepRequest,
    TextSelectVariantRequest,
    TextSpecialInstructionRequest,
    TextConfirmOrderRequest
)
from core import process_order_step_one, get_closest_variant


router = APIRouter()


@router.post("/fri-der-man/handle-order/text/first-step", tags=["text-input"])
def handle_first_step(payload: TextFirstStepRequest):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    inp = payload.model_dump()
    try:
        logger.info(f"Processing step one of the order")
        founditems = process_order_step_one(inp['text'])
    except BaseException as ex:
        message = f"Got error while processing the order = {str(ex)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

    inp['items'].extend(founditems)
    # by default cancel flag will be false
    inp['cancel_flag'] = False
    return inp


@router.post("/fri-der-man/handle-order/text/select-variant", tags=["text-input"])
def select_variant(payload: TextSelectVariantRequest):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    inp = payload.model_dump()
    try:
        item_index = inp['item_index']
        possible_variants = inp['items'][item_index]['possiblevariants']
    except:
        message = f"Couldn't able to extract possible variants from the item index = {item_index}"
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    try:
        logger.info(f"Selecting the closest variant from possible variants = {possible_variants}")
        matchedflag, matched_variant = get_closest_variant(inp['text'], possible_variants)
    except BaseException as ex:
        message = f"Got error while selecting variant = {str(ex)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

    # deleting the possible variants key from the dict
    if matchedflag:
        del inp['items'][item_index]['possiblevariants']
        inp['items'][item_index]['variantflag'] = False
        inp['items'][item_index]['matched_variant'] = matched_variant
        inp['items'][item_index]['message'] = f"You have chosen {matched_variant}"
        inp['items'][item_index]['special_instruction'] = True
    else:
        inp['items'][item_index]['message'] = f"No variant has been matched. Please try again!!"

    # by default cancel flag will be false
    inp['cancel_flag'] = False

    return inp


@router.post("/fri-der-man/handle-order/text/special-instructions", tags=["text-input"])
def handle_special_instructions(payload: TextSpecialInstructionRequest):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    inp = payload.model_dump()
    try:
        item_index = inp['item_index']
        item_info = inp['items'][item_index]
    except:
        message = f"Couldn't able to extract item info from the item index = {item_index}"
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    item_info['special_instruction'] = inp['text']
    # by default cancel flag will be false
    inp['cancel_flag'] = False

    return inp


@router.post("/fri-der-man/handle-order/text/order-confirmation", tags=["text-input"])
def order_confirmation(payload: TextConfirmOrderRequest):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    inp = payload.model_dump()
    text = inp['text'].lower()

    if "yes" in text:
        confirm = True
        message = "Thank you for your order. It's being processed."
    else:
        confirm = False
        message = "Your order has not been confirmed. Please start over."

    inp['message'] = message
    inp['confirm'] = confirm
    inp['cancel_flag'] = False

    return inp
