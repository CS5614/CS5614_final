from pydantic import BaseModel

class QoLScore(BaseModel):
    id: int
    qolScore: float