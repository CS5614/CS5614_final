from server.models.rental_score_model import RentalScoreModel
from typing import List
from fastapi import APIRouter, HTTPException, Query
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from utils.convert_qol import QualityOfLifeConverter

router = APIRouter(prefix="/api/rentalScore", tags=["rentalScore"])

@router.get("", response_model=List[RentalScoreModel])
async def get_rental_score():

    converter = QualityOfLifeConverter()
    all_scores = converter.fetch_rental_scores()
    if not all_scores:
        raise HTTPException(status_code=404, detail="No records found")
    return all_scores


@router.get("", response_model=List[RentalScoreModel])
async def get_rental_score(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, gt=0, le=1000, description="Max records to return"),
):

    converter = QualityOfLifeConverter()
    all_scores = converter.fetch_rental_scores()
    page = all_scores[skip: skip + limit]

    if not page and skip > 0:
        raise HTTPException(status_code=404, detail="No records found")
    return page