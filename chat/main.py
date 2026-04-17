from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid6 import uuid7
from database import SessionLocal, engine
from models import Base, Profile
from utils import get_age_group, utc_now
from services import fetch_all

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS
@app.middleware("http")
async def add_cors(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/profiles")
async def create_profile(payload: dict, db: Session = Depends(get_db)):

    name = payload.get("name")

    if name is None or name == "":
        return JSONResponse(status_code=400, content={
            "status": "error",
            "message": "Missing or empty name"
        })

    if not isinstance(name, str):
        return JSONResponse(status_code=422, content={
            "status": "error",
            "message": "Invalid type"
        })

    name = name.lower()

    # Idempotency
    existing = db.query(Profile).filter(Profile.name == name).first()
    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": serialize(existing)
        }

    try:
        gender_data, age_data, nation_data = await fetch_all(name)
    except Exception:
        return JSONResponse(status_code=502, content={
            "status": "error",
            "message": "Upstream failure"
        })

    # -------- VALIDATIONS -------- #

    if gender_data.get("gender") is None or gender_data.get("count", 0) == 0:
        return JSONResponse(status_code=502, content={
            "status": "error",
            "message": "Genderize returned an invalid response"
        })

    if age_data.get("age") is None:
        return JSONResponse(status_code=502, content={
            "status": "error",
            "message": "Agify returned an invalid response"
        })

    countries = nation_data.get("country", [])
    if not countries:
        return JSONResponse(status_code=502, content={
            "status": "error",
            "message": "Nationalize returned an invalid response"
        })

    top_country = max(countries, key=lambda x: x["probability"])


    profile = Profile(
        id=str(uuid7()),
        name=name,
        gender=gender_data["gender"],
        gender_probability=gender_data["probability"],
        sample_size=gender_data["count"],
        age=age_data["age"],
        age_group=get_age_group(age_data["age"]),
        country_id=top_country["country_id"],
        country_probability=top_country["probability"],
        created_at=utc_now()
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "status": "success",
        "data": serialize(profile)
    }


@app.get("/api/profiles/{id}")
def get_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "status": "success",
        "data": serialize(profile)
    }


@app.get("/api/profiles")
def get_profiles(
    gender: str = None,
    country_id: str = None,
    age_group: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Profile)

    if gender:
        query = query.filter(Profile.gender.ilike(gender))

    if country_id:
        query = query.filter(Profile.country_id.ilike(country_id))

    if age_group:
        query = query.filter(Profile.age_group.ilike(age_group))

    results = query.all()

    return {
        "status": "success",
        "count": len(results),
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "gender": p.gender,
                "age": p.age,
                "age_group": p.age_group,
                "country_id": p.country_id
            } for p in results
        ]
    }


@app.delete("/api/profiles/{id}", status_code=204)
def delete_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.delete(profile)
    db.commit()
    return None


def serialize(p):
    return {
        "id": p.id,
        "name": p.name,
        "gender": p.gender,
        "gender_probability": p.gender_probability,
        "sample_size": p.sample_size,
        "age": p.age,
        "age_group": p.age_group,
        "country_id": p.country_id,
        "country_probability": p.country_probability,
        "created_at": p.created_at.isoformat().replace("+00:00", "Z")
    }