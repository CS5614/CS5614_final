from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal

class PriceParams(BaseModel):
    weight: float = Field(..., ge=0)
    direction: Literal["positive", "negative"] = Field("negative")

class QoLWeightRequest(BaseModel):
    # Make price to receive either positive or negative direction
    price: Optional[PriceParams] = None

    airQualityScore: Optional[float] = Field(None, ge=0)
    walkScore: Optional[float] = Field(None, ge=0)
    nearestBusStopDistance: Optional[float] = Field(None, ge=0)
    busStopsNumber: Optional[float] = Field(None, ge=0)
    nearestParkDistance: Optional[float] = Field(None, ge=0)
    openStreetNumber: Optional[float] = Field(None, ge=0)

    def normalize(self) -> Dict[str, float]:
        """
        Normalize weights so that they sum to 1. If all weights are zero or None, raise ValueError.
        Returns:
            A dictionary with normalized weights.
        """
        active_features = {}
        items = self.model_dump()

        # Handle price separately
        price_params = items.get("price")
        if price_params and isinstance(price_params, dict) and price_params.get("weight", 0) > 0:
            active_features["price"] = price_params

        # Handle other features
        for name, weight in items.items():
            if name != "price" and isinstance(weight, (int, float)) and weight > 0:
                active_features[name] = {"weight": weight}

        if not active_features:
            raise ValueError("At least one feature with weight > 0 must be provided.")

        total_weight = sum(params["weight"] for params in active_features.values())
        if total_weight == 0:
            raise ValueError("Total weight cannot be zero.")

        normalized_data = {}
        for name, params in active_features.items():
            normalized_data[name] = {
                "weight": params["weight"] / total_weight,
                # 如果是 price，則從請求中讀取 direction；否則預設為 None
                "direction": params.get("direction")
            }
        return normalized_data
