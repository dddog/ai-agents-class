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
