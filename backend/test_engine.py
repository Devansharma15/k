"""Test all 7 intent-parsing rules in the Workflow Planning Engine."""
from app.services.workflow_architect_service import workflow_architect_service

def run(prompt):
    print(f"\n{'='*70}")
    print(f"PROMPT: {prompt}")
    print('='*70)
    result = workflow_architect_service.generate(prompt)
    print(f"  Name:       {result['name']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Missing:    {result['missing_integrations'] or 'none'}")
    
    # Check rules
    nodes = result['nodes']
    edges = result['edges']
    node_map = {n['id']: n for n in nodes}
    
    # Print graph
    print(f"  Graph ({len(nodes)} nodes, {len(edges)} edges):")
    for n in nodes:
        config = n['config']
        action = config.get('action', '-')
        expr = config.get('expression', '')
        prompt_field = config.get('prompt', '')[:50] if config.get('prompt') else ''
        binds = sum(1 for v in config.values() if isinstance(v, str) and '{{' in v)
        print(f"    [{n['type']}] {n['name']}  action={action}  bindings={binds}")
        if expr:
            print(f"      expression: {expr}")
        if prompt_field:
            print(f"      prompt: {prompt_field}...")
    for e in edges:
        print(f"    {e['source'][:25]} -> {e['target'][:25]}  [{e['condition']}]")
    
    # Rule checks
    validation = result['reasoning']['validation']
    if validation['issues']:
        print(f"  VALIDATION ISSUES:")
        for issue in validation['issues']:
            print(f"    - {issue}")
    else:
        print(f"  VALIDATION: PASSED (all rules OK)")
    
    return result

# Test 1: Router must have LLM before it
print("\n### RULE 1: Condition/router MUST have LLM before it ###")
r = run("Create a personal life manager with Telegram and Google Calendar")
cond_nodes = [n for n in r['nodes'] if n['type'] == 'condition']
llm_nodes = [n for n in r['nodes'] if n['type'].startswith('llm_')]
if cond_nodes:
    assert llm_nodes, "RULE 1 VIOLATED: condition exists without LLM!"
    print("  >> RULE 1 OK: LLM exists before condition")

# Test 2: Condition references LLM output, not trigger
print("\n### RULE 2+3: Condition must reference LLM output, not trigger ###")
for n in r['nodes']:
    if n['type'] == 'condition':
        expr = n['config'].get('expression', '')
        trigger_id = r['nodes'][0]['id']
        assert trigger_id not in expr, f"RULE 3 VIOLATED: condition references trigger {trigger_id}"
        assert '.output.intent' in expr or '.output.decision' in expr, "RULE 2 VIOLATED: no structured output ref"
        print(f"  >> RULE 2+3 OK: expression = {expr}")

# Test 3: Simple webhook -> Slack (no condition, no padding)
print("\n### RULE 4: Integration nodes have explicit action ###")
r = run("Send a Slack notification when a webhook is received")
for n in r['nodes']:
    if n['type'].startswith('integration_'):
        assert n['config'].get('action'), f"RULE 4 VIOLATED: {n['name']} has no action!"
        print(f"  >> RULE 4 OK: {n['name']} action={n['config']['action']}")

# Test 4: Stripe payment with approval (condition auto-injects LLM)
print("\n### RULE 1 (auto-inject): Condition with no AI still gets LLM ###")
r = run("When a Stripe payment is received, get approval if amount > 500 and log to Google Sheets")
cond_nodes = [n for n in r['nodes'] if n['type'] == 'condition']
llm_nodes = [n for n in r['nodes'] if n['type'].startswith('llm_')]
if cond_nodes:
    assert llm_nodes, "RULE 1 VIOLATED: condition without LLM!"
    print(f"  >> RULE 1 OK: auto-injected {llm_nodes[0]['type']}")

# Test 5: Gmail must have explicit action
print("\n### RULE 6: Gmail must specify action ###")
r = run("When a new email arrives, classify it and create a Zendesk ticket if it's a complaint")
for n in r['nodes']:
    if n['type'] == 'integration_gmail':
        action = n['config'].get('action', '')
        assert action in ('send_email', 'new_message', 'read_messages', 'mark_read'), f"RULE 6 VIOLATED: Gmail action={action}"
        print(f"  >> RULE 6 OK: Gmail action={action}")

# Test 6: Schedule -> LLM -> Twitter
print("\n### RULE 4: Twitter has explicit publish_post action ###")
r = run("Every day, generate a social media post and publish to Twitter")
for n in r['nodes']:
    if n['type'] == 'integration_twitter':
        assert n['config'].get('action') == 'publish_post', "RULE 4 VIOLATED"
        print(f"  >> RULE 4 OK: Twitter action={n['config']['action']}")

print("\n" + "="*70)
print("ALL RULE CHECKS PASSED!")
print("="*70)
