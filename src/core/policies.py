def planner_to_research(policy_input):
    return policy_input.state.plan_confidence < 0.9

graph.add_edge("Planner", "Researcher-Web", policy=planner_to_research)
