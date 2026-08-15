import hashlib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from config import settings

router = APIRouter(prefix="/api/click", tags=["click"])


def make_md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


@router.post("/prepare")
async def click_prepare(request: Request):
    form = await request.form()

    click_trans_id = str(form.get("click_trans_id", ""))
    service_id = str(form.get("service_id", ""))
    click_paydoc_id = str(form.get("click_paydoc_id", ""))
    merchant_trans_id = str(form.get("merchant_trans_id", ""))
    amount = str(form.get("amount", ""))
    action = str(form.get("action", ""))
    sign_time = str(form.get("sign_time", ""))
    sign_string = str(form.get("sign_string", ""))

    expected_sign = make_md5(
        click_trans_id
        + service_id
        + settings.click_secret_key
        + merchant_trans_id
        + amount
        + action
        + sign_time
    )

    if sign_string != expected_sign:
        return JSONResponse(
            {
                "click_trans_id": int(click_trans_id or 0),
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": 0,
                "error": -1,
                "error_note": "SIGN CHECK FAILED",
            }
        )

    return JSONResponse(
        {
            "click_trans_id": int(click_trans_id or 0),
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": int(click_trans_id or 0),
            "error": 0,
            "error_note": "Success",
        }
    )


@router.post("/complete")
async def click_complete(request: Request):
    form = await request.form()

    click_trans_id = str(form.get("click_trans_id", ""))
    service_id = str(form.get("service_id", ""))
    merchant_trans_id = str(form.get("merchant_trans_id", ""))
    merchant_prepare_id = str(form.get("merchant_prepare_id", ""))
    amount = str(form.get("amount", ""))
    action = str(form.get("action", ""))
    sign_time = str(form.get("sign_time", ""))
    sign_string = str(form.get("sign_string", ""))

    expected_sign = make_md5(
        click_trans_id
        + service_id
        + settings.click_secret_key
        + merchant_trans_id
        + merchant_prepare_id
        + amount
        + action
        + sign_time
    )

    if sign_string != expected_sign:
        return JSONResponse(
            {
                "click_trans_id": int(click_trans_id or 0),
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": 0,
                "error": -1,
                "error_note": "SIGN CHECK FAILED",
            }
        )

    return JSONResponse(
        {
            "click_trans_id": int(click_trans_id or 0),
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": int(click_trans_id or 0),
            "error": 0,
            "error_note": "Success",
        }
    )
