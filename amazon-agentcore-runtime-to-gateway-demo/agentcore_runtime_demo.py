import agent_core_utils
from strands import Agent
import logging
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import os
import requests
import json
import os
import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp


def get_auth_info() :
    REGION = os.environ['AWS_DEFAULT_REGION']
    USER_POOL_NAME = "sample-agentcore-gateway-pool"
    RESOURCE_SERVER_ID = "sample-agentcore-gateway-id"
    RESOURCE_SERVER_NAME = "sample-agentcore-gateway-name"
    CLIENT_NAME = "sample-agentcore-gateway-client"
    SCOPES = [
        {"ScopeName": "gateway:read", "ScopeDescription": "Read access"},
        {"ScopeName": "gateway:write", "ScopeDescription": "Write access"}
    ]
    scopeString = f"{RESOURCE_SERVER_ID}/gateway:read {RESOURCE_SERVER_ID}/gateway:write"

    cognito = boto3.client("cognito-idp", region_name=REGION)

    print("Creating or retrieving Cognito resources...")
    user_pool_id = agent_core_utils.get_or_create_user_pool(cognito, USER_POOL_NAME)
    print(f"User Pool ID: {user_pool_id}")

    agent_core_utils.get_or_create_resource_server(cognito, user_pool_id, RESOURCE_SERVER_ID, RESOURCE_SERVER_NAME,
                                                    SCOPES)
    print("Resource server ensured.")

    client_id, client_secret = agent_core_utils.get_or_create_m2m_client(cognito, user_pool_id, CLIENT_NAME,
                                                                          RESOURCE_SERVER_ID)
    print(f"Client ID: {client_id}")
    print(f"Client secret: {client_secret}")
    print(f"scopeString: {scopeString}")

    # Get discovery URL
    cognito_discovery_url = f'https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration'
    print(cognito_discovery_url)
    return user_pool_id, client_id, client_secret, scopeString

def get_auth_token(user_pool_id, client_id, client_secret,scopeString) :
   print("Requesting the access token from Amazon Cognito authorizer...May fail for some time till the domain name propogation completes")
   token_response = agent_core_utils.get_token(user_pool_id, client_id, client_secret,scopeString,os.environ['AWS_DEFAULT_REGION'])
   token = token_response["access_token"]
   print("Token response:", token)
   return token

def create_streamable_http_transport(mcp_url: str, access_token: str):
       return streamablehttp_client(
           mcp_url,
           #timeout=1,
           headers={"Authorization": f"Bearer {access_token}"})


def get_full_tools_list(client):
    """
    List tools w/ support for pagination
    """
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            more_tools = True
            pagination_token = tmp_tools.pagination_token
    return tools


print("start initilization")
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

gateway_url = "${YOU_GATEWAY_URL}"

app = BedrockAgentCoreApp()

print("app started")

@app.entrypoint
#async
def invoke(payload):
    print("agent invoked")
    """Process user input and return a response"""
    prompt = payload.get("prompt")
    print("prompt : "+prompt)
    model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    temperature=0.7)

    user_pool_id, client_id, client_secret, scopeString = get_auth_info()
    access_token = get_auth_token(user_pool_id, client_id, client_secret, scopeString)

    mcp_client = MCPClient(lambda: create_streamable_http_transport(gateway_url, access_token))

    with mcp_client:
        tools = get_full_tools_list(mcp_client)
        print(f"Found the following tools: {[tool.tool_name for tool in tools]}")

        agent= Agent(model=model, tools=tools)

        #agent("Give me the information about order with id 12345 ")
        #agent('In case you found the order, can you provide the information about the user who made #this purchase')
        #agent('Can you list orders created between 1 of August 2025 5am and 5 of August 2025 3am. '
            # 'Please use the following date format, for example: 2025-08-02T19:50:55')
        #agent('What is the total value of all these orders together?')

        return agent(prompt)

        #stream = agent.stream_async(prompt)
        #async for event in stream:
            #print(event)
            #yield (event)


if __name__ == "__main__":
    app.run()