from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Allows select origin, crea to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # allows all origins
    allow_credentials=False, # Indicates that cookies should be supported for cross origin requests, the default is False
    allow_methods=["*"], # this allows all http methods to communicate or perform cross origin requests
    allow_headers=["*"], # allows all http request headers to communicate
)

# stores the base url of the exteranl API
GENDERIZE_URL = "https://api.genderize.io"

# To customize each error message
def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message},
    )


def utc_now_iso() -> str:
    # Noting the time for every request
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@app.get("/api/classify")
async def classify_name(name: Optional[Any] = Query(default=None)):
    # Missing
    if name is None:
        return error_response("Missing required query parameter: name", 400)

    # Non-string
    if not isinstance(name, str):
        return error_response("The 'name' query parameter must be a string", 422)

    # Empty string or whitespace-only
    cleaned_name = name.strip()
    if cleaned_name == "":
        return error_response("Missing required query parameter: name", 400)

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(GENDERIZE_URL, params={"name": cleaned_name})
            response.raise_for_status()
            payload = response.json()

    except httpx.HTTPStatusError:
        return error_response("Failed to get a valid response from Genderize API", 502)
    except httpx.RequestError:
        return error_response("Unable to reach Genderize API", 502)
    except Exception:
        return error_response("Internal server error", 500)

    gender = payload.get("gender")
    probability = payload.get("probability")
    count = payload.get("count", 0)

    if gender is None or count == 0:
        return error_response("No prediction available for the provided name", 502)

    try:
        probability = float(probability)
        sample_size = int(count)
    except (TypeError, ValueError):
        return error_response("Invalid response received from Genderize API", 502)

    is_confident = probability >= 0.7 and sample_size >= 100

    return {
        "status": "success",
        "data": {
            "name": cleaned_name,
            "gender": gender,
            "probability": probability,
            "sample_size": sample_size,
            "is_confident": is_confident,
            "processed_at": utc_now_iso(),
        },
    }