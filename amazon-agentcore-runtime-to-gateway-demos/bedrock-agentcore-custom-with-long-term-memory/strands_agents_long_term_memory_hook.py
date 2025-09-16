from typing import Dict

from strands.hooks import AfterInvocationEvent, HookProvider, HookRegistry, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient

class LongTermMemoryHookProvider(HookProvider):

    def __init__(self, memory_client: MemoryClient, memory_id: str):
        self.memory_id = memory_id
        self.memory_client = memory_client
        self.namespaces = self.get_namespaces()

    # Helper function to get namespaces from memory strategies list
    def get_namespaces(self) :
        """Get namespace mapping for memory strategies."""
        try:
            strategies = self.memory_client.get_memory_strategies(self.memory_id)
            return {i["type"]: i["namespaces"][0] for i in strategies}
        except Exception as e:
            print(f"Failed to extract memory strategis: {e}")


    def retrieve_context(self, event:  MessageAddedEvent):
        """Retrieve customer context before processing support query"""
        print("Retrieving customer context before processing support query")
        messages = event.agent.messages
        if messages[-1]["role"] == "user" and "toolResult" not in messages[-1]["content"][0]:
            user_query = messages[-1]["content"][0]["text"]
            print(f"User query: {user_query}")
            try:
                # Retrieve customer context from all namespaces
                all_context = []

                # Get actor_id from agent state
                actor_id = event.agent.state.get("actor_id")
                if not actor_id:
                    print("Missing actor_id in agent state")
                    return
                session_id = event.agent.state.get("session_id")

                for context_type, namespace in self.namespaces.items():
                    print(f"before: Context: {context_type} namespace: {namespace}")
                    namespace = namespace.format(actorId=actor_id, sessionId=session_id)
                    print(f"after: Context: {context_type} namespace: {namespace}")
                    memories = self.memory_client.retrieve_memories(
                        memory_id=self.memory_id,
                        namespace=namespace.format(actorId=actor_id, sessionId=session_id),
                        query=user_query,
                        top_k=3
                    )

                    for memory in memories:
                        if isinstance(memory, dict):
                            content = memory.get('content', {})
                            if isinstance(content, dict):
                                text = content.get('text', '').strip()
                                if text:
                                    all_context.append(f"[{context_type.upper()}] {text}")

                # Inject customer context into the query
                if all_context:
                    context_text = "\n".join(all_context)
                    original_text = messages[-1]["content"][0]["text"]
                    messages[-1]["content"][0]["text"] = (
                        f"Customer Context:\n{context_text}\n\n{original_text}"
                    )
                    print(f"Retrieved {len(all_context)} customer context items")
                    print(f"Retrieved {context_text} context text")
                    print(f"Retrieved {original_text} original text")

            except Exception as e:
                print(f"Failed to retrieve customer context: {e}")

    def save_event(self, event: AfterInvocationEvent):
        """Save support interaction after agent response"""
        print("Saving support interaction after agent response")
        try:
            messages = event.agent.messages
            if len(messages) >= 2 and messages[-1]["role"] == "assistant":
                # Get last customer query and agent response
                customer_query = None
                agent_response = None

                for msg in reversed(messages):
                    if msg["role"] == "assistant" and not agent_response:
                        agent_response = msg["content"][0]["text"]
                    elif msg["role"] == "user" and not customer_query and "toolResult" not in msg["content"][0]:
                        customer_query = msg["content"][0]["text"]
                        break
                print(f"Customer Query: {customer_query} Agent Response: {agent_response}")
                if customer_query and agent_response:
                    # Get session info from agent state
                    actor_id = event.agent.state.get("actor_id")
                    session_id = event.agent.state.get("session_id")

                    if not actor_id or not session_id:
                        print("Missing actor_id or session_id in agent state")
                        return

                    # Save the support interaction
                    self.memory_client.create_event(
                        memory_id=self.memory_id,
                        actor_id=actor_id,
                        session_id=session_id,
                        messages=[(customer_query, "USER"), (agent_response, "ASSISTANT")]
                    )
                    print("Saved support interaction to memory")
                    print((customer_query, "USER"), (agent_response, "ASSISTANT"))

        except Exception as e:
            print(f"Failed to save support interaction: {e}")

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register customer support memory hooks"""
        registry.add_callback(MessageAddedEvent, self.retrieve_context)
        registry.add_callback(AfterInvocationEvent, self.save_event)

