import os
import json
import uuid
from tqdm import tqdm
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Load environment variables
load_dotenv()

# Configuration
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../dataset"))
EMBEDDING_MODEL = "text-embedding-3-small"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = "math-content"
BATCH_SIZE = 100

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def read_all_json_paths(root_dir: str) -> List[str]:
    all_json_files = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                all_json_files.append(os.path.join(subdir, file))
    return all_json_files

def load_valid_data(file_paths: List[str]) -> List[dict]:
    all_data = []
    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            problem = data.get("problem", "").strip()
            solution = data.get("solution", "").strip()
            if not problem or not solution:
                continue

            all_data.append({
                "id": str(uuid.uuid4()),
                "text": f"{problem}\nSolution: {solution}",
                "payload": {
                    "content_id": str(uuid.uuid4()),
                    "solution": solution,
                    "problem": problem,
                    "section": data.get("type", os.path.basename(os.path.dirname(path))),
                    "difficulty_level": data.get("level", ""),
                }
            })

        except Exception as e:
            print(f" Skipped {path}: {e}")
    return all_data

def batch(iterable, batch_size):
    """Yield successive batch-sized chunks from iterable"""
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

def embed_and_upload(data_batch: List[dict]):
    try:
        texts = [item["text"] for item in data_batch]
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        embeddings = [res.embedding for res in response.data]

        points = []
        for i, item in enumerate(data_batch):
            points.append(PointStruct(
                id=item["id"],
                vector=embeddings[i],
                payload=item["payload"]
            ))

        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

    except Exception as e:
        print(f"Batch failed: {e}")

def main():
   
    file_paths = read_all_json_paths(ROOT_DIR)
    all_data = load_valid_data(file_paths)
    
    for data_batch in tqdm(batch(all_data, BATCH_SIZE), total=(len(all_data) // BATCH_SIZE + 1)):
        embed_and_upload(data_batch)

if __name__ == "__main__":
    main()
