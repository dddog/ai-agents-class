from pydantic import BaseModel
from typing import Optional, List

class RestaurantContext(BaseModel):
    customer_id: int
    name: str
    preferred_language: str = "Korean"
    reservation_details: Optional[dict] = None
    order_items: List[dict] = []

class HandoffData(BaseModel):
    to_agent_name: str
    reason: str
    issue_description: Optional[str] = None

class RestaurantInputGuardrailOutput(BaseModel):
    is_off_topic: bool
    is_inappropriate: bool
    reason: str

class RestaurantOutputGuardrailOutput(BaseModel):
    is_unprofessional_or_impolite: bool
    exposes_internal_info: bool
    reason: str

