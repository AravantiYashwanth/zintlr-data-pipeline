from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from schemas import CompanyResponse
from db import companies_cleaned

app = FastAPI(
    title="Zintlr Company API",
    version="1.0.0"
)

# ---------- Request Schema ----------
class CompanyRequest(BaseModel):
    cin: str


# ---------- Health Check ----------
@app.get("/")
def health_check():
    return {"status": "API is running"}


# ---------- Fetch Company ----------
@app.post("/company", response_model=CompanyResponse)
def get_company(payload: CompanyRequest):
    company = companies_cleaned.find_one({"cin": payload.cin})

    if not company:
        raise HTTPException(status_code=404, detail="CIN not found")

    # 🔴 MongoDB cleanup
    company.pop("_id", None)

    # 🔴 Type safety
    if "registration_number" in company and company["registration_number"] is not None:
        company["registration_number"] = str(company["registration_number"])

    return company
