import os
from bedrock_agentcore.memory import MemoryClient

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
ACTOR_ID = "order_statistics_user_123" # It can be any unique identifier (AgentID, User ID, etc.)
SESSION_ID = "order_statistics_session_001" # Unique session identifier

# Initialize Memory Client
client = MemoryClient(region_name=os.environ['AWS_DEFAULT_REGION'])
memory_id="{YOUR_MEMORY_ID}"


# Check what's stored in memory
print("=== Memory Contents ===")
recent_turns = client.get_last_k_turns(
    memory_id=memory_id,
    actor_id=ACTOR_ID,
    session_id=SESSION_ID,
    k=7 # Adjust k to see more or fewer turns
)

for i, turn in enumerate(recent_turns, 1):
    print(f"Turn {i}:")
    for message in turn:
        role = message['role']
        content = message['content']['text'][:1000] + "..." if len(message['content']['text']) > 100 else message['content']['text']
        print(f"  {role}: {content}")
    print()

strategies = client.get_memory_strategies(memory_id)

strategies_str={i["type"]: i["namespaces"][0] for i in strategies}
print(strategies_str)