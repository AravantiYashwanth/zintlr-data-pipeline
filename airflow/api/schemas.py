from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CompanyResponse(BaseModel):
    cin: str
    name: str
    company_status: str
    date_of_incorporation: datetime

    roc: Optional[str] = None
    registration_number: Optional[str] = None
    company_category: Optional[str] = None
    company_sub_category: Optional[str] = None
    company_class: Optional[str] = None
    authorized_capital: Optional[int] = None
    paid_up_capital: Optional[int] = None
    listed_status: Optional[str] = None
    nic_code: Optional[int] = None
    nic_description: Optional[str] = None
    number_of_members: Optional[int] = None
    company_age_years: Optional[int] = None
    source_url: Optional[str] = None
    scraped_at: Optional[datetime] = None
    cleaned_at: Optional[datetime] = None

    class Config:
        from_attributes = True
