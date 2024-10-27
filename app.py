# app.py

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import uuid
import redis.asyncio as redis
import json
from config import config

# Use Redis configuration from config
redis_host = config['redis']['host']
redis_port = config['redis']['port']
redis_db = config['redis']['db']
redis_password = config['redis']['password']

def generate_job_id():
    # Generate an 8-character alphanumeric string
    return uuid.uuid4().hex[:8]

async def lifespan(app: FastAPI):
    # Initialize Redis client
    app.state.redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
        decode_responses=True  # Decode responses to strings
    )
    yield
    # Close the Redis connection
    await app.state.redis_client.close()

app = FastAPI(lifespan=lifespan)

@app.post("/submit")
async def submit_job(
    prompt: str = Form(...),
    image: UploadFile = File(...)
):
    redis_client = app.state.redis_client

    # Read image bytes
    image_bytes = await image.read()
    # Generate job_id
    job_id = generate_job_id()
    # Store job data in Redis
    job_data = {
        'job_id': job_id,
        'prompt': prompt,
        'image': image_bytes.hex(),  # Store image bytes as hex string
        'status': 'waiting',
    }
    job_key = f'job:{job_id}'
    # Store job data as a hash
    await redis_client.hset(job_key, mapping=job_data)
    # Push job_id onto the queue
    await redis_client.rpush('job_queue', job_id)
    return {'job_id': job_id}

@app.get("/status/{job_id}")
async def check_status(job_id: str):
    redis_client = app.state.redis_client

    job_key = f'job:{job_id}'
    exists = await redis_client.exists(job_key)
    if not exists:
        raise HTTPException(status_code=404, detail="Job not found")
    job_data = await redis_client.hgetall(job_key)
    status = job_data.get('status')
    if status in ['waiting', 'processing']:
        return JSONResponse(content={'status': status}, status_code=202)
    elif status == 'done':
        # Retrieve the result
        result = job_data.get('result')
        # Parse the JSON result
        result_data = json.loads(result)
        return JSONResponse(content=result_data, status_code=200)
    else:
        raise HTTPException(status_code=500, detail="Unknown job status")

if __name__ == '__main__':
    import uvicorn
    server_host = config['server']['host']
    server_port = config['server']['port']
    uvicorn.run("app:app", host=server_host, port=server_port)
