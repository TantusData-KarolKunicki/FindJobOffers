from typing import List

from langchain_core.pydantic_v1 import BaseModel, Field


class JobOffer(BaseModel):
    job_name: str = Field(description="Job position name")
    job_link: str = Field(description="The url to the job offer")


class JobOffers(BaseModel):
    job_offers: List[JobOffer] = Field(...)


class JobBoard(BaseModel):
    job_board: str = Field(description=" The job board link")
