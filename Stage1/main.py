from fastapi import FastAPI, HTTPException, Query, Response
import httpx
from database import db, name_index
from utils import generate_id, utc_now, classify_age
from models import ProfileCreate

app = FastAPI()

# CORS (required)
@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


# -------- Helper: Call APIs --------
async def fetch_data(name: str):
    async with httpx.AsyncClient() as client:
        gender_res = await client.get(f"https://api.genderize.io?name={name}")
        age_res = await client.get(f"https://api.agify.io?name={name}")
        nation_res = await client.get(f"https://api.nationalize.io?name={name}")

    return gender_res.json(), age_res.json(), nation_res.json()


# -------- POST /api/profiles --------
@app.post("/api/profiles", status_code=201)
async def create_profile(payload: ProfileCreate):

    name = payload.name.strip().lower()

    if not name:
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "message": "Missing or empty name"
        })

    # Idempotency
    if name in name_index:
        existing = db[name_index[name]]
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": existing
        }

    gender_data, age_data, nation_data = await fetch_data(name)

    # ---- Genderize validation ----
    if gender_data.get("gender") is None or gender_data.get("count", 0) == 0:
        raise HTTPException(status_code=502, detail={
            "status": "error",
            "message": "Genderize returned an invalid response"
        })

    # ---- Agify validation ----
    if age_data.get("age") is None:
        raise HTTPException(status_code=502, detail={
            "status": "error",
            "message": "Agify returned an invalid response"
        })

    # ---- Nationalize validation ----
    countries = nation_data.get("country", [])
    if not countries:
        raise HTTPException(status_code=502, detail={
            "status": "error",
            "message": "Nationalize returned an invalid response"
        })

    top_country = max(countries, key=lambda x: x["probability"])

    profile = {
        "id": generate_id(),
        "name": name,
        "gender": gender_data["gender"],
        "gender_probability": gender_data["probability"],
        "sample_size": gender_data["count"],
        "age": age_data["age"],
        "age_group": classify_age(age_data["age"]),
        "country_id": top_country["country_id"],
        "country_probability": top_country["probability"],
        "created_at": utc_now()
    }

    db[profile["id"]] = profile
    name_index[name] = profile["id"]

    return {
        "status": "success",
        "data": profile
    }


# -------- GET /api/profiles/{id} --------
@app.get("/api/profiles/{id}")
async def get_profile(id: str):
    if id not in db:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "message": "Profile not found"
        })

    return {
        "status": "success",
        "data": db[id]
    }


# -------- GET /api/profiles --------
@app.get("/api/profiles")
async def list_profiles(
    gender: str = Query(None),
    country_id: str = Query(None),
    age_group: str = Query(None)
):

    results = list(db.values())

    if gender:
        results = [p for p in results if p["gender"].lower() == gender.lower()]

    if country_id:
        results = [p for p in results if p["country_id"].lower() == country_id.lower()]

    if age_group:
        results = [p for p in results if p["age_group"].lower() == age_group.lower()]

    response_data = [
        {
            "id": p["id"],
            "name": p["name"],
            "gender": p["gender"],
            "age": p["age"],
            "age_group": p["age_group"],
            "country_id": p["country_id"]
        }
        for p in results
    ]

    return {
        "status": "success",
        "count": len(response_data),
        "data": response_data
    }


# -------- DELETE /api/profiles/{id} --------
@app.delete("/api/profiles/{id}", status_code=204)
async def delete_profile(id: str):
    if id not in db:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "message": "Profile not found"
        })

    name = db[id]["name"]
    del db[id]
    del name_index[name]

    return Response(status_code=204)