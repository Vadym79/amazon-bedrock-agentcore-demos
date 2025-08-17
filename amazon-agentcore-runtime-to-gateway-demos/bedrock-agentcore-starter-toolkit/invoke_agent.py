import boto3
import json
import os

# Initialize the Bedrock AgentCore client
agent_core_client = boto3.client('bedrock-agentcore', region_name=os.environ['AWS_DEFAULT_REGION'])


# Prepare the payload
#payload = json.dumps({"prompt": "'Can you list orders created between 1 of August 2025 5am and 7 of August 2025 3am. "
 #                               "Please use the following date format, for example: 2025-08-02T19:50:55"})

payload = json.dumps({"prompt": "Give me the information about order with id 12344"})

print(payload)


response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn="{YOUR_RUNTIME_ARN}",
    qualifier="DEFAULT",
    payload=payload
)

print(response)
if "text/event-stream" in response.get("contentType", ""):
    content = []
    for line in response["response"].iter_lines(chunk_size=1):
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                line = line[6:]
                print(line)
                content.append(line)
else:
   response_body = response['response'].read()
   response_data = json.loads(response_body)
   print("Agent Response:", response_data)

print("end")


