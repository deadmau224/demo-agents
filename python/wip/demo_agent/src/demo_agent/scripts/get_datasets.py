from dotenv import load_dotenv
from galileo.datasets import get_dataset

# Load environment variables with explicit path
load_dotenv()
# Also try loading from parent directories in case of path issues
load_dotenv("../../.env")
load_dotenv("../.env")

# Get a dataset by name
# dataset = get_dataset(
#     name="countries"
# )

# Get a dataset by ID
dataset = get_dataset(id="c9b09652-5158-49d7-9fce-eec131a96aec")

# Get its content
data = dataset.get_content()

print(data)
