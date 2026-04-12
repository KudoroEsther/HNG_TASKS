# Gender Classify API

This project provides a GET endpoint at `/api/classify` that accepts a `name` query parameter, calls the Genderize API, processes the result, and returns a structured response.

The API is built with **FastAPI** and includes:
- Input validation
- Processed response formatting
- Error handling
- CORS support
- UTC timestamp generation for every request
---

## Requirements

- Python 3.8+
- pip

---

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Server

```bash
uvicorn genderize:app --reload
```

The server starts at `http://localhost:8000` by default.

To use a different port:

```bash
uvicorn genderize:app --reload --port 8080
```

---

## API Reference

### `GET /api/classify`

Classifies a name by predicted gender using the Genderize.io API.

**Query Parameters**

| Parameter | Type   | Required | Description          |
|-----------|--------|----------|----------------------|
| `name`    | string | Yes      | The name to classify |

**Example Request**

```
GET http://localhost:8000/api/classify?name=James
```

**Success Response — `200 OK`**

```json
{
  "status": "success",
  "data": {
    "name": "James",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-12T10:00:00Z"
  }
}
```

**Field Descriptions**

| Field          | Description                                                           |
|----------------|-----------------------------------------------------------------------|
| `name`         | The name that was classified (whitespace-trimmed)                    |
| `gender`       | Predicted gender: `"male"` or `"female"`                             |
| `probability`  | Confidence score from Genderize.io (0.0 – 1.0)                       |
| `sample_size`  | Number of data points used for the prediction (renamed from `count`) |
| `is_confident` | `true` only when `probability >= 0.7` AND `sample_size >= 100`       |
| `processed_at` | UTC timestamp of when the request was processed (ISO 8601)           |

---

## Error Responses

All errors follow this consistent structure:

```json
{
  "status": "error",
  "message": "<description of the error>"
}
```

| Scenario                               | Status Code | Message                                            |
|----------------------------------------|-------------|----------------------------------------------------|
| `name` is missing                      | `400`       | Missing required query parameter: name             |
| `name` is empty or whitespace only     | `400`       | Missing required query parameter: name             |
| `name` is not a string                 | `422`       | The 'name' query parameter must be a string        |
| No gender prediction available         | `502`       | No prediction available for the provided name      |
| Genderize.io returned a bad status     | `502`       | Failed to get a valid response from Genderize API  |
| Genderize.io is unreachable            | `502`       | Unable to reach Genderize API                      |
| Malformed data from Genderize.io       | `502`       | Invalid response received from Genderize API       |
| Unexpected server error                | `500`       | Internal server error                              |

---

## CORS

All responses include the following header to allow cross-origin access from any client:

```
Access-Control-Allow-Origin: *
```

---

## How `is_confident` Works

The `is_confident` flag is `true` only when **both** of the following conditions are met:

- `probability >= 0.7` — the prediction is at least 70% confident
- `sample_size >= 100` — the prediction is backed by at least 100 data points

If either condition fails, `is_confident` is `false`.

---

## Implementation Notes

- **HTTP client:** Uses `httpx.AsyncClient` with a 3-second timeout to call Genderize.io.
- **Name sanitization:** Leading and trailing whitespace is stripped before the API call.
- **`processed_at` timestamp:** Generated fresh on every request using `datetime.now(timezone.utc)` — never hardcoded.
- **Response format:** `count` from Genderize.io is renamed to `sample_size` in the response.
