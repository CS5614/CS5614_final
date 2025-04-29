from pydantic import BaseModel


class RentalScoreModel(BaseModel):
    id: int
    lat: float
    long: float
    name: str
    qolScore: float
    walkScore: float
    airQualityScore: float
    busStopsNumber: int
    nearestBusStopDistance: float
    openStreetNumber: int
    nearestParkDistance: float
    reviewScore: float
    price: float
    bedroom: float
    bathroom: float
    state: str
    address: str
