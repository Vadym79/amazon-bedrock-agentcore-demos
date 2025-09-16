import os
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError
from bedrock_agentcore.memory.constants import StrategyType

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Define memory strategies for customer support
strategies = [
    #{
      #  StrategyType.USER_PREFERENCE.value: {
       #     "name": "CustomerPreferences",
       #     "description": "Captures customer preferences and behavior",
       #     "namespaces": ["support/customer/{actorId}/preferences"]
        #}
    #},
    {
        StrategyType.SUMMARY.value: {
            "name": "CustomerSummary",
            "description": "Captures customer summary",
            "namespaces": ["support/customer/{actorId}/{sessionId}/summary"]
        }
    },

    {
        StrategyType.SEMANTIC.value: {
            "name": "CustomerSupportSemantic",
            "description": "Stores facts from conversations",
            "namespaces": ["support/customer/{actorId}/semantic"],
        }
    }
]

# Initialize Memory Client
client = MemoryClient(region_name=os.environ['AWS_DEFAULT_REGION'])
memory_name = "OrderStatisticsAgentMemoryWithStrategies"

try:
    # Create memory resource without strategies (thus only access to short-term memory)
    memory = client.create_memory_and_wait(
        name=memory_name,
        strategies=strategies,
        description="Long-term memory for personal agent",
        event_expiry_days=7, # Retention period for short-term memory. This can be upto 365 days.
    )
    memory_id = memory['id']
    print(f"✅ Created memory: {memory_id}")
except ClientError as e:
    print(f"❌ ERROR: {e}")
    if e.response['Error']['Code'] == 'ValidationException' and "already exists" in str(e):
        # If memory already exists, retrieve its ID
        memories = client.list_memories()
        memory_id = next((m['id'] for m in memories if m['id'].startswith(memory_name)), None)
        print(f"Memory already exists. Using existing memory ID: {memory_id}")
except Exception as e:
    # Show any errors during memory creation
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    # Cleanup on error - delete the memory if it was partially created
    if memory_id:
        try:
            client.delete_memory_and_wait(memory_id=memory_id)
            print(f"Cleaned up memory: {memory_id}")
        except Exception as cleanup_error:
            print(f"Failed to clean up memory: {cleanup_error}")
