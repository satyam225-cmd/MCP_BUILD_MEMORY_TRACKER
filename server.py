from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import os


# Load environment variables from .env file
load_dotenv()
# Initialize OpenAI client
client = OpenAI()

VECTOR_STORE_NAME = "MEMORIES"

# Create FastAPI app
mcp = FastMCP("Memories")

def get_or_create_vector_store():

    stores = client.vector_stores.list()
    for store in stores:
        if store.name == VECTOR_STORE_NAME:
            return store
    return client.vector_stores.create(name=VECTOR_STORE_NAME)

# Save input string to vector store as a file and return the vector store ID for retrieval later
@mcp.tool()
def save_memory(memory: str):
    vector_store = get_or_create_vector_store()
    with tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".txt") as f:
        f.write(memory)
        f.flush()
        client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=open(f.name, "rb")
        )
    return {"Status": "saved", "memory_store_id": vector_store.id}


# Search for a string in the vector store and return the most relevant memory

@mcp.tool()
def retrieve_memory(query: str):  
    vector_store = get_or_create_vector_store()
    results = client.vector_stores.search(
        vector_store_id=vector_store.id,
        query=query,
    )
    content_text =[
        content.text 
        for result in results.data
        for content in result.content
        if content.type == "text"
    ]
    return {"results": content_text}

    # if results.data:  
    #     return {"Status": "found", "memory": results.data[0].metadata.text}
    # else:
    #     return {"Status": "not found", "memory": None}

if __name__ == "__main__":
    mcp.run()
