import uuid

from loguru import logger
from fastapi import APIRouter
from fastapi import UploadFile, File, HTTPException, Depends

from models import PossibleVariantsRequest
from core import process_audio, process_order_step_one, get_closest_variant


router = APIRouter()


@router.post("/fri-der-man/handle-order/file/first-step", tags=["audio-file-upload"])
def handle_first_step(payload: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    try:
        logger.info(f"Performing speech recognition on the upload file = {payload.filename}")
        text = process_audio(payload.file)
        founditems = process_order_step_one(text)
    except BaseException as ex:
        message = f"Got error while performing recognizing speech = {str(ex)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

    response = {
        "id": uid,
        "filename": payload.filename,
        "text": text,
        "items": founditems
    }
    return response


@router.post("/fri-der-man/handle-order/file/select-variant", tags=['audio-file-upload'])
def select_variant(payload: UploadFile = File(...), variants: PossibleVariantsRequest = Depends()):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    try:
        logger.info(f"Performing speech recognition on the upload file = {payload.filename}")
        text = process_audio(payload.file)
        matchedflag, matched_variant = get_closest_variant(text, variants.possiblevariants)
    except BaseException as ex:
        message = f"Got error while selecting variant = {str(ex)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

    response = {
        "uid": uid,
        "text": text,
        "variant_match": matchedflag,
        "matched_variant": matched_variant
    }
    return response


@router.post("/fri-der-man/handle-order/file/special-instructions", tags=['audio-file-upload'])
def handle_special_instructions(payload: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    try:
        logger.info(f"Performing speech recognition on the upload file = {payload.filename}")
        text = process_audio(payload.file)
    except BaseException as ex:
        message = f"Got error while performing recognizing speech = {str(ex)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

    response = {
        "id": uid,
        "filename": payload.filename,
        "text": text
    }
    return response


@router.post("/fri-der-man/handle-order/file/order-confirmation", tags=['audio-file-upload'])
def order_confirmation(payload: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    logger.info(f"Generated request id = {uid}")

    try:
        logger.info(f"Performing speech recognition on the upload file = {payload.filename}")
        text = process_audio(payload.file)
    except BaseException as ex:
        message = f"Got error while performing recognizing speech = {str(ex)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

    confirm = True if "yes" in text else False

    if "yes" in text:
        confirm = True
        message = "Thank you for your order. It's being processed."
    else:
        confirm = False
        message = "Your order has not been confirmed. Please start over."

    response = {
        "id": uid,
        "filename": payload.filename,
        "confirm": confirm,
        "message": message,
        "text": text
    }
    return response
