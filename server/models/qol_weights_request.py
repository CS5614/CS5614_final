from pydantic import BaseModel, Field
from typing import Optional, Dict

class QoLWeightRequest(BaseModel):
    price: Optional[float] = Field(None, ge=0)
    airQualityScore: Optional[float] = Field(None, ge=0)
    walkScore: Optional[float] = Field(None, ge=0)
    nearestBusStopDistance: Optional[float] = Field(None, ge=0)
    busStopsNumber: Optional[float] = Field(None, ge=0)
    nearestParkDistance: Optional[float] = Field(None, ge=0)
    openStreetNumber: Optional[float] = Field(None, ge=0)

    def normalize(self) -> Dict[str, float]:
        items = {k: v for k, v in self.model_dump().items() if v is not None and v > 0}
        if not items: raise ValueError("At least one weight > 0 must be provided.")
        total = sum(items.values())
        return {k: v / total for k, v in items.items()}
