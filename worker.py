# worker.py

import asyncio
import redis.asyncio as redis
import json
import io
from config import config

from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
from PIL import Image
import torch

class Worker:
    def __init__(self):
        # Use Redis configuration from config
        redis_host = config['redis']['host']
        redis_port = config['redis']['port']
        redis_db = config['redis']['db']
        redis_password = config['redis']['password']

        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )

        self.max_pixels = 250000 #300'000 max pixels  #increase if u got more than 12GB VRAM

    async def __aenter__(self):
        await self.setup() #skip setup locally
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.redis_client.aclose()

    async def setup(self, device='auto'):
        # Load the processor
        self.processor = AutoProcessor.from_pretrained(
            "cyan2k/molmo-7B-O-bnb-4bit", #'allenai/Molmo-7B-D-0924', <- use this if you have like 24 GB of VRAM or maybe 16GB even works.. i have 12
            trust_remote_code=True,
            torch_dtype='auto',
            device_map=device
        )

        # Load the model
        self.model = AutoModelForCausalLM.from_pretrained(
            "cyan2k/molmo-7B-O-bnb-4bit",
            trust_remote_code=True,
            torch_dtype='auto',
            device_map=device
        )

        #cast model to lower precision weights (eeek)
        #self.model.to(dtype=torch.bfloat16) #maybe remove this on server with nice GPU

    def decode_request(self, job_data):
        # Extract image bytes and prompt from job_data
        image_hex = job_data.get('image')
        image_bytes = bytes.fromhex(image_hex)
        prompt = job_data.get('prompt')
        return (image_bytes, prompt)

    def predict(self, input_data, max_tokens=200):
        image_bytes, prompt = input_data
        print("image bytes",image_bytes)
        print("prompt",prompt)
        print("split")
        image = self.resize_image(Image.open(io.BytesIO(image_bytes)).convert('RGB'))
        print("got image")
        image.show()
        inputs = self.processor.process(
            images=[image],
            text=prompt
        )
        print("set inputs")
        inputs = {k: v.to(self.model.device).unsqueeze(0) for k, v in inputs.items()}
        print("iterated inputs")
        '''
        output = self.model.generate_from_batch(
            inputs,
            GenerationConfig(max_new_tokens=2000, stop_strings="<|endoftext|>"),
            tokenizer=self.processor.tokenizer,
        )
        '''
        #inputs['images'] = inputs['images'].to(torch.bfloat16) #remove on server too perhaps
        #na thise above is making it fuck out I think.. maybe. lol. commented it out. gave hallucinatory responses
        
        #with torch.autocast(device_type="cuda", enabled=True, dtype=torch.bfloat16): #this also didnt do any favors id rather have an OOM
        output = self.model.generate_from_batch(
            inputs,
            GenerationConfig(max_new_tokens=max_tokens, stop_strings="<|endoftext|>"),
            tokenizer=self.processor.tokenizer) #woah should it only be 200 tokens max output didnt it use to be 2000 lol
        #OK so ^^ i increased the max tokens from 200 to 600 cause what if theres lots of form fields? yea.
        #but if replies are ALWAYS too long now then lower it to 200 again.
        #OR set it ?? default 200. so you do 200 on elements, when pointing to one thing, and 600 when DESCRIBING yes! soon implement. time time time
        
        print("generated output")
        generated_tokens = output[0, inputs['input_ids'].size(1):]
        print("got tokens generated")
        return self.processor.tokenizer.decode(generated_tokens, skip_special_tokens=True)

    def encode_response(self, result):
        return result

    def resize_image(self, image): #u dont have to resize if you have dank VRAM. i will soon this is going to a server today. woohoo! finally can play COD again no more CONSTANT MOlmo inference :'D
        current_pixels = image.width*image.height
        if current_pixels <= self.max_pixels:
            return image
        else:
            scale_factor = (self.max_pixels / current_pixels) ** 0.5 #huh
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            print("screenshot orginal size is",(image.height),"*",(image.width), "=", (image.height * image.width), "pixels")
            print("screenshot new size is",(new_height),"*",(new_width), "=", (new_height*new_width), "pixels")
            return image.resize((new_width, new_height), Image.LANCZOS)

    async def process_job(self, job_id):
        job_key = f'job:{job_id}'
        # Get job data
        job_data = await self.redis_client.hgetall(job_key)
        # Update status to 'processing'
        await self.redis_client.hset(job_key, 'status', 'processing')
        #print("RAW JOB_DATA:",job_data) #for debugging , u have error unpack values here ^ 
        # Process the job
        print(f"Processing job {job_id}...")

        try:
            # Decode request
            print("Decoding request...")
            input_data = self.decode_request(job_data)
            print("input_data:",input_data)
            print("Decoded request!")
            # Predict
            print("Predicting...")
            result = self.predict(input_data)
            print("Done!")
            # Encode response
            print("Encoding...")
            encoded_result = self.encode_response(result)
            print("Encoded! Done!")

            # Store result in Redis
            print("Storing result in Redis...")
            await self.redis_client.hset(job_key, mapping={
                'status': 'done',
                'result': json.dumps({'message': encoded_result})
            })
            print(f"Job {job_id} done.")

        except Exception as e:
            print(f"Error processing job {job_id}: {e}")
            # Update status to 'failed'
            await self.redis_client.hset(job_key, 'status', 'failed')

    async def run(self):
        try:
            while True:
                # Use BLPOP to get job_id from the queue
                job = await self.redis_client.blpop('job_queue', timeout=0)
                if job:
                    # BLPOP returns a tuple (queue_name, job_id)
                    _, job_id = job
                    print("Received the job! Ready to work on it!",job_id)
                    await self.process_job(job_id)
                    #pretend!
        except Exception as e:
            print(f"Worker error: {e}")

async def main():
    worker = Worker()
    async with worker:
        await worker.run()

if __name__ == '__main__':
    asyncio.run(main())
