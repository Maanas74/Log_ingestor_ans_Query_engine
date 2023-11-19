from fastapi import FastAPI, BackgroundTasks, Request
import uvicorn
from models.validation import Log_ingestion
from sqlalchemy import Column,String,DateTime,Table,MetaData
from sqlalchemy.dialects.postgresql import JSONB
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from databases import Database
from elasticsearch import Elasticsearch
from fastapi.middleware.cors import CORSMiddleware


app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set this to the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metadata= MetaData()


#connecting to the elasticsearch
es = Elasticsearch([{"scheme":"http","host":"127.0.0.1","port":9200}],http_auth=("elastic", "maanas"))

 
templates = Jinja2Templates(directory="Template")

#Creating the logs table
logs_table = Table(
    "logs",
    metadata,
    Column("level", String),
    Column("message", String),
    Column("resourceid", String),
    Column("timestamp", DateTime),
    Column("traceid", String, primary_key=True),
    Column("spanid", String),
    Column("commit", String),
    Column("metadata", JSONB),
)


def index_to_elasticsearch(log_data: dict):
    # Index log data to Elasticsearch
    es.index(index='logs_index', body=log_data)
    


@app.post("/")
async def add_log(data: Log_ingestion, background_tasks: BackgroundTasks):
    log_data = data.dict()
    log_data["timestamp"] = datetime.utcnow()

    background_tasks.add_task(index_to_elasticsearch, log_data)

    return {"message": "Log storage request accepted"}


#Used for searching data from the ElasticSearch
@app.post("/search")
async def query_logs(request: Request):
    
    data = await request.json()

    filters = data.get("filters", {})
    count= int(data.get("count",0))

    es_query = {
    "query": {
        "bool": {
            "must": [
                {"match": {key: value}} if key != "parentResourceId" else
                {"match": {"metadata.parentResourceId": value}}
                for key, value in filters.items() if value
            ]
        }}}


    result = es.search(index='logs_index', body=es_query,from_=count,size=10)

    logs_search_result = [hit["_source"] for hit in result["hits"]["hits"]]

    return logs_search_result


#Render the HTML with the FastAPI
@app.get("/", response_class=HTMLResponse)
async def get_search_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})




if __name__=="__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=3000, reload=True)
    