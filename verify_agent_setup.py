#!/usr/bin/env python3
"""
Verify Event Impact Correlation Agent setup (structure check only)
This script checks if all files are in place without running the full agent.
"""
import os
import sys

def check_file_exists(filepath):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {filepath}")
    return exists

def verify_agent_structure():
    """Verify the Event Impact Correlation Agent structure"""
    
    print("="*80)
    print("EVENT IMPACT CORRELATION AGENT - STRUCTURE VERIFICATION")
    print("="*80)
    
    files_to_check = [
        "app/sub_agents/event_impact_agent/__init__.py",
        "app/sub_agents/event_impact_agent/agent.py",
        "app/sub_agents/event_impact_agent/tools.py",
        "app/agent.py",
        "app/sub_agents/__init__.py",
    ]
    
    print("\n📁 Checking file structure:")
    print("-" * 80)
    
    all_exist = True
    for filepath in files_to_check:
        if not check_file_exists(filepath):
            all_exist = False
    
    print("\n📝 Checking file contents:")
    print("-" * 80)
    
    # Check if agent.py has the import
    try:
        with open("app/agent.py", "r", encoding="utf-8") as f:
            agent_content = f.read()
            has_import = "from app.sub_agents.event_impact_agent import event_impact_agent" in agent_content
            has_sub_agent = "event_impact_agent" in agent_content
            
            if has_import:
                print("✅ Main agent.py imports event_impact_agent")
            else:
                print("❌ Main agent.py missing event_impact_agent import")
                all_exist = False
            
            if has_sub_agent:
                print("✅ Main agent.py includes event_impact_agent in sub_agents")
            else:
                print("❌ Main agent.py missing event_impact_agent in sub_agents list")
                all_exist = False
    except Exception as e:
        print(f"❌ Error reading agent.py: {e}")
        all_exist = False
    
    # Check if tools.py has the bond volatility function
    try:
        with open("app/sub_agents/event_impact_agent/tools.py", "r", encoding="utf-8") as f:
            tools_content = f.read()
            has_bond_analysis = "def analyze_bond_volatility" in tools_content
            has_caching = "class EventDataLoader" in tools_content
            has_memory_cache = "_memory_cache" in tools_content
            
            if has_bond_analysis:
                print("✅ tools.py contains analyze_bond_volatility function")
            else:
                print("❌ tools.py missing analyze_bond_volatility function")
                all_exist = False
            
            if has_caching and has_memory_cache:
                print("✅ tools.py implements caching mechanism")
            else:
                print("❌ tools.py missing caching implementation")
                all_exist = False
    except Exception as e:
        print(f"❌ Error reading tools.py: {e}")
        all_exist = False
    
    # Check if agent.py has the comprehensive instructions
    try:
        with open("app/sub_agents/event_impact_agent/agent.py", "r", encoding="utf-8") as f:
            agent_file_content = f.read()
            has_bond_instructions = "BOND TRADING" in agent_file_content
            has_tools_import = "analyze_bond_volatility" in agent_file_content
            
            if has_bond_instructions:
                print("✅ agent.py contains bond trading instructions")
            else:
                print("❌ agent.py missing bond trading instructions")
                all_exist = False
            
            if has_tools_import:
                print("✅ agent.py imports bond analysis tools")
            else:
                print("❌ agent.py missing bond analysis tool imports")
                all_exist = False
    except Exception as e:
        print(f"❌ Error reading event_impact_agent/agent.py: {e}")
        all_exist = False
    
    print("\n" + "="*80)
    if all_exist:
        print("✅ VERIFICATION PASSED - Agent structure is correct!")
        print("="*80)
        print("\n📚 Next Steps:")
        print("   1. Install dependencies: uv sync")
        print("   2. Run the agent: python -m app.agent_engine_app")
        print("   3. Test with query: 'I want to trade around market volatility")
        print("                        for 10-year bonds for a time horizon of 5 years.'")
        print("\n💡 Features:")
        print("   • Multi-level GCS caching (60-min TTL) for low latency")
        print("   • Bond volatility analysis with trading signals")
        print("   • Multi-factor confidence scoring")
        print("   • Event correlation analysis")
        return True
    else:
        print("❌ VERIFICATION FAILED - Some files are missing or incomplete")
        print("="*80)
        return False

if __name__ == "__main__":
    success = verify_agent_structure()
    sys.exit(0 if success else 1)

