import boto3
import json
import os

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
# Initialize the Bedrock AgentCore client
agent_core_client = boto3.client('bedrock-agentcore')

payload = json.dumps({
     "input": {"prompt": "Hi, my name is Vadym. Today is a sunny weather. Give me the information about order with id 1230"}
})

#payload = json.dumps({
 #    "input": {"prompt": "Hi, give me the information about order with id 1225"}
#})

#payload = json.dumps({
    # "input": {"prompt": "Please summarize all orders you already have information about"}
#})

#payload = json.dumps({
 #    "input": {"prompt": "Tell me please: what is my name and how is the weather today?"}
#})


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