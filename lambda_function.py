# lambda_function.py
import json
import os
import tempfile
import boto3
from rag_chain import load_chain         # your ingestion logic
from agent import create_agent       # your ReACT agent setup

s3 = boto3.client("s3")
BUCKET = os.environ["S3_BUCKET_NAME"]


# Module-level cache
_cached_s3_key   = None
_cached_agent    = None

def lambda_handler(event, context):
    
    global _cached_s3_key, _cached_agent
    
    if "body" in event and event["body"]:
        payload = json.loads(event["body"])
    else:
        payload = event
        

    # 1. Validate input
    s3_key = payload.get("s3_key")
    query  = payload.get("query")
    if not s3_key or not query:
        return {"statusCode":400, "body": json.dumps({"error":"Missing s3_key or query"})}

    # 2. If this is a new PDF (or first call), rebuild the chain
    if s3_key != _cached_s3_key:
        tmp_dir = tempfile.gettempdir()
        local_path = os.path.join(tmp_dir, os.path.basename(s3_key))
        
        # local_path = f"/tmp/{os.path.basename(s3_key)}"
        s3.download_file(BUCKET, s3_key, local_path)
        
        # 3. Build the retriever on this PDF
        retriever = load_chain(local_path)
        
        # 4. Create the agent
        _cached_agent   = create_agent(retriever)
        _cached_s3_key  = s3_key

    # result = agent.run(query)
    result = _cached_agent.invoke({"input": query})['output']

    # 5. Return the answer
    return {
        "statusCode": 200,
        "body": json.dumps({"answer": result})
    }
