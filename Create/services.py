import httpx

GENDERIZE_URL = "https://api.genderize.io"
AGIFY_URL = "https://api.agify.io"
NATIONALIZE_URL = "https://api.nationalize.io"


async def fetch_all(name: str):
    async with httpx.AsyncClient() as client:
        gender_res, age_res, nation_res = await client.gather(
            client.get(GENDERIZE_URL, params={"name": name}),
            client.get(AGIFY_URL, params={"name": name}),
            client.get(NATIONALIZE_URL, params={"name": name}),
        )

    return gender_res.json(), age_res.json(), nation_res.json()