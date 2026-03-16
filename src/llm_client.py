import os
import boto3
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# We configure Bedrock runtime client. Boto3 will automatically look for
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION in env vars or ~/.aws/credentials.
# Defaulting to us-east-1 for Nova models if region is not set, though it should ideally be set in the environment.

aws_region = os.getenv("AWS_REGION", "us-east-1")
try:
    client = boto3.client("bedrock-runtime", region_name=aws_region)
except Exception as e:
    print(f"WARNING: Could not initialize Bedrock client. Ensure AWS credentials are set: {e}")

def query_nova(prompt, system_instruction=None, model_name="us.amazon.nova-2-lite-v1:0", response_schema=None):
    """
    Sends a prompt to Amazon Nova via AWS Bedrock Converse API and returns the text response.
    Supports structured output instructions if response_schema is provided.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]

        system_prompts = []
        if system_instruction:
            system_prompts.append({"text": system_instruction})

        # Tool configuration for structured output via Converse API
        tool_config = None
        if response_schema:
            # We wrap the Pydantic JSON schema into an AWS Bedrock tool config
            # Nova will be forced to output this structure.
            tool_config = {
                "tools": [
                    {
                        "toolSpec": {
                            "name": "structured_output",
                            "description": "Output the mandatory structured JSON response exactly matching this schema.",
                            "inputSchema": {
                                "json": response_schema
                            }
                        }
                    }
                ],
                "toolChoice": {
                    "tool": {
                        "name": "structured_output"
                    }
                }
            }

        args = {
            "modelId": model_name,
            "messages": messages,
            "inferenceConfig": {"temperature": 0.3}
        }

        if system_prompts:
            args["system"] = system_prompts

        if tool_config:
            args["toolConfig"] = tool_config

        response = client.converse(**args)
        
        # If we asked for structured output, the response will be a tool use block
        if tool_config:
             for content_block in response['output']['message']['content']:
                 if 'toolUse' in content_block:
                     # Return the raw JSON dictionary returned by the tool as a string,
                     # to match the previous gemini `response_text` behavior for Pydantic parsing
                     import json
                     return json.dumps(content_block['toolUse']['input'])
             return "Error: Model did not use the structured output tool."
        else:
             # Standard text response
             return response['output']['message']['content'][0]['text']

    except Exception as e:
        return f"Error querying Amazon Nova: {str(e)}"
