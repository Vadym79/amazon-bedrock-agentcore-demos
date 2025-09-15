from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime,timezone
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from strands_agents_short_term_memory_hook import ShortTermMemoryHookProvider
from bedrock_agentcore.memory import MemoryClient

import os
import requests
import json
import os
import boto3
import agent_core_utils
import logging


# Initialize Memory Client


ACTOR_ID = "order_statistics_user_123" # It can be any unique identifier (AgentID, User ID, etc.)
SESSION_ID = "order_statistics_session_001" # Unique session identifier

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
client = MemoryClient(region_name=os.environ['AWS_DEFAULT_REGION'])
memory_id="{YOUR_MEMORY_ID}"
gateway_url = "${YOUR_GATEWAY_URL}"

app = FastAPI(title="Strands Agent Server", version="1.0.0")

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]


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


@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    print("agent invoked")
    try:
        prompt = request.input.get("prompt", "")
        print("prompt : " + prompt)
        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        #model = BedrockModel(
           # model_id="us.amazon.nova-pro-v1:0",
           # temperature=0.7)

        user_pool_id, client_id, client_secret, scopeString = get_auth_info()
        access_token = get_auth_token(user_pool_id, client_id, client_secret, scopeString)

        mcp_client = MCPClient(lambda: create_streamable_http_transport(gateway_url, access_token))

        with mcp_client:
            tools = get_full_tools_list(mcp_client)
            print(f"Found the following tools: {[tool.tool_name for tool in tools]}")

            agent = Agent(
                                #model=model,  #use the default Bedrock Model which is Anthropic Claude Sonnet 
                                tools=tools,
                                system_prompt="Please answer the questions about the order statistics. "
                                                "If you received a personal information about the user you chat with "
                                                "or this user told you during previous conversation some facts like about the weather or his mood, "
                                                "feel free to also provide it in your answer. If you don't have the answer to such questions please tell it so.",
                                hooks=[ShortTermMemoryHookProvider(client, memory_id)],
                                state={"actor_id": ACTOR_ID, "session_id": SESSION_ID})
            result = agent(prompt)

        response = {
            "message": result.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "strands-agent",
        }

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)