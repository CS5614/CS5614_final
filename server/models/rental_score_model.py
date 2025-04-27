from pydantic import BaseModel

class RentalScoreModel(BaseModel):
    lat:              float
    long:             float
    name:             str
    qolScore:         float
    walkScore:        float
    airQualityScore:  float
    busStopsNumber:   int
    openStreetNumber: int
    reviewScore:      float
    price:            float
    bedroom:          float
    bathroom:         float
    state:            str

