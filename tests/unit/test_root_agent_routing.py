def test_root_agent_routes_realtime_volatility_to_realtime_agent():
    from app.agent import root_agent
    from app.sub_agents.realtime_alerts import realtime_alerts_agent

    instr = root_agent.instruction.lower()
    assert "realtimealertsagent" in instr.replace(' ', '') or "realtimealerts" in instr
    # ensure specific tool reference is present
    assert "detect_high_volatility" in root_agent.instruction
    # ensure agent is registered as a sub-agent
    assert realtime_alerts_agent in root_agent.sub_agents
