import asyncio
from orbit.integrations.langgraph.trace import trace_agent
from orbit.integrations.ollama.client import OllamaClient
from orbit.security.guardrail import SecurityGuard
from orbit.database.models import RunRecord
from orbit.database.session import AsyncSessionLocal
from sqlalchemy import select

# We wrap the main execution to simulate an agent flow
@trace_agent(agent_name="coding_agent", task="Write a python function for QuickSort", model_name="llama3.1")
async def run_agent():
    print("Initializing Coding Agent...")
    client = OllamaClient()
    guard = SecurityGuard()
    
    # Retrieve the active run ID to associate security events
    run_id = 1
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(RunRecord).order_by(RunRecord.id.desc()).limit(1))
        run = res.scalar_one_or_none()
        if run:
            run_id = run.id

    prompt = "Write a python function for QuickSort."
    
    print("Checking prompt security...")
    await guard.scan_input(run_id, prompt)
    
    print("Generating response...")
    try:
        response = await client.generate("llama3.1", prompt)
        print("Response received.")
        
        await guard.scan_output(run_id, response.get("response", ""))
        return response
    except Exception as e:
        print(f"Error during generation: {e}")
        raise e
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(run_agent())
