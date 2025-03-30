from anthropic import AnthropicBedrock
import os
from dotenv import load_dotenv

load_dotenv()

aws_access_key = os.getenv("AWS_BEDROCK_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_BEDROCK_SECRET_KEY")
aws_region = os.getenv("AWS_BEDROCK_REGION")
region_prefix = os.getenv("AWS_BEDROCK_REGION_PREFIX")
model_base = os.getenv("AWS_BEDROCK_MODEL_BASE")


client = AnthropicBedrock(
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    aws_region=aws_region
)

model_id = f"{region_prefix}.{model_base}"
if model_base.startswith(f"{region_prefix}."):
    model_id = model_base 

try:
    message = client.messages.create(
        model=model_id,
        max_tokens=200,
        temperature=1,
        top_p=0.999,
        top_k=250,
        messages=[{"role": "user", "content": "hello world"}]
    )
    print(message.content)
except Exception as e:
    print(f"Error calling Claude: {e}")