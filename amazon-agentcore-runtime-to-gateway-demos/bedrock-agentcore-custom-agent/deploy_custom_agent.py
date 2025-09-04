import boto3
import os

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
client = boto3.client('bedrock-agentcore-control')

response = client.create_agent_runtime(
    agentRuntimeName='strands_custom_agent',
    agentRuntimeArtifact={
        'containerConfiguration': {
            'containerUri': '{YOUR_ECR_REPO_URI}'
        }
    },
    networkConfiguration={"networkMode": "PUBLIC"},
    roleArn='{YOUR_IAM_ROLE_ARN}'
)

print(f"Agent Runtime created successfully!")
print(f"Agent Runtime ARN: {response['agentRuntimeArn']}")
print(f"Status: {response['status']}")