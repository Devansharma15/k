"""Test Semantic Routing in the Workflow Planning Engine."""
from app.services.workflow_architect_service import workflow_architect_service
import time

def run(prompt):
    print(f"\n{'='*70}")
    print(f"PROMPT: {prompt}")
    print('='*70)
    
    start = time.time()
    result = workflow_architect_service.generate(prompt)
    duration = time.time() - start
    
    print(f"  Name:       {result['name']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Duration:   {duration:.2f}s")
    
    # Check rules
    nodes = result['nodes']
    edges = result['edges']
    
    # Print graph
    print(f"  Graph ({len(nodes)} nodes, {len(edges)} edges):")
    for n in nodes:
        config = n['config']
        action = config.get('action', '-')
        print(f"    [{n['type']}] {n['name']}  (action={action})")
    
    print(f"  Reasoning:")
    print(f"    Trigger: {result['reasoning']['trigger_reason']}")
    print(f"    Tools Selected:")
    for t in result['reasoning']['selected_tools']:
        print(f"      - {t['type']} (reason: {t['reason']})")
        
    return result

# Test 1: Ambiguous wording that requires semantic routing
print("\n### SEMANTIC ROUTER TEST ###")
run("When a bill comes in, get someone to review it then log it.")

# Test 2: Another ambiguous query
run("Let the team know when a task is finished via chat app.")
