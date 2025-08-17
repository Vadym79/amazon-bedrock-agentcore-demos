## Example of how to run deploy and invoke Amazon Bedrock [AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html)

In this example I use [Strands Agents](https://strandsagents.com/latest/) talking to the AgentCore Gateway.  

## Prerequisites:  

 Already created AgentCore Gateway URL, for example with [Lambda Target](https://github.com/Vadym79/AWSLambdaJavaWithAmazonDSQL/blob/main/sample-app-with-pgjdbc/src/main/resources/AmazonBedrockAgentCoreGateway_Lambda_Function_Target.ipynb) or [API Gateway Taget](https://github.com/Vadym79/AWSLambdaJavaWithAmazonDSQL/blob/main/sample-app-with-pgjdbc/src/main/resources/AmazonBedrockAgentCoreGateway_API_Gateway_REST_API.ipynb).  
 Please read my article [Amazon Bedrock AgentCore Gateway - Part 2 Exposing existing Amazon API Gateway REST API via MCP and Gateway endpoint](https://dev.to/aws-heroes/amazon-bedrock-agentcore-gateway-part-2-exposing-existing-amazon-api-gateway-rest-api-via-mcp-and-4458) with the step by step instructions about to create AgentCore Gateway URL with the existing API Gateway Target.

My agent implemention which talks to the agent which has the BedrockAgentCoreApp decorated entrypoint is in the [agentcore_runtime_demo.py](https://github.com/Vadym79/amazon-bedrock-agentcore-demos/blob/main/amazon-agentcore-runtime-to-gateway-demo/agentcore_runtime_demo.py) script.
Please replace the value of the variable gatewayurl= "${YOU_GATEWAY_URL}" in the [agentcore_runtime_demo.py](https://github.com/Vadym79/amazon-bedrock-agentcore-demos/blob/main/amazon-agentcore-runtime-to-gateway-demo/agentcore_runtime_demo.py) with the valid created AgentCore Gateway URL.

## AgentCore Runtime configuration and deployment


Here are the examples of how to [deploy Strands Agents to Amazon Bedrock AgentCore Runtime](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/). 

Please follow the instructions and then execute the following to configure the agent :



```bash
agentcore configure --entrypoint agentcore_runtime_demo.py -er IAM_ARN 
```


IAM role should have the following [permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html) or you can auto-create it by leaving -er parameter. As we also access CognitoPool, please add the following permissions and replace the region and account_id with your values to the execution policy:

    {
            "Effect": "Allow",
            "Action": [
                "cognito-idp:ListUserPools"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cognito-idp:DescribeUserPool",
                "cognito-idp:DescribeResourceServer",
                "cognito-idp:ListUserPoolClients",
                "cognito-idp:DescribeUserPoolClient"
            ],
            "Resource": [
                "arn:aws:cognito-idp:{region}:{account_id}:userpool/*"
            ]
        },

Then invoke agent core with the sample prompt as below:


```bash
agentcore invoke '{"prompt": "Give me the information about order with id 12345"}' 
```

You can do the same with Python SDK by running [agentcore_runtime_demo_invoke.py](https://github.com/Vadym79/amazon-bedrock-agentcore-demos/blob/main/amazon-agentcore-runtime-to-gateway-demo/agentcore_runtime_demo_invoke.py) script.    
Please replace the value of the variable agentRuntimeArn="{YOUR_RUNTIME_ARN}" in this file with the valid Agentcore Runtime ARN deployed in the previous step (agentcore configure) 

For more examples please view the article [Deploying Strands Agents to Amazon Bedrock AgentCore Runtime](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/). 
