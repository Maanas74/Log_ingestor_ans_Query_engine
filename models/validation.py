from datetime import datetime
from pydantic import BaseModel, Field,ConfigDict


class metadata(BaseModel):
    parentResourceId : str

class Log_ingestion(BaseModel):
    level: str
    message: str
    resourceid: str = Field(alias="resourceId")
    timestamp: datetime
    traceid: str = Field(alias="traceId")
    spanid: str = Field(alias="spanId")
    commit: str
    metadata: metadata
    
    model_config = ConfigDict(
        populate_by_name=True,
    )
    