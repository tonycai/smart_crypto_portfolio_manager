#!/usr/bin/env python3
"""
Script to directly modify the orchestration agent to use localhost instead of hostnames
"""
import os
import re
import sys

def update_agent_file(file_path):
    """
    Update agent file to use localhost instead of hostnames
    
    Args:
        file_path: Path to agent file
    """
    if not os.path.exists(file_path):
        print(f"Error: Agent file {file_path} not found")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace hostnames with localhost in the default config section
        pattern_dict = {
            r'"market_analysis_agent_url": "http://market-analysis-agent:(\d+)"': r'"market_analysis_agent_url": "http://localhost:\1"',
            r'"trade_execution_agent_url": "http://trade-execution-agent:(\d+)"': r'"trade_execution_agent_url": "http://localhost:\1"',
            r'"risk_management_agent_url": "http://risk-management-agent:(\d+)"': r'"risk_management_agent_url": "http://localhost:\1"',
            r'"reporting_analytics_agent_url": "http://reporting-analytics-agent:(\d+)"': r'"reporting_analytics_agent_url": "http://localhost:\1"'
        }
        
        # Replace hostnames in all code
        for pattern, replacement in pattern_dict.items():
            content = re.sub(pattern, replacement, content)
        
        # Save updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Updated agent code in {file_path}")
        return True
    
    except Exception as e:
        print(f"Error updating agent code: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 update_orchestration_agent.py <agent_file_path>")
        print("Example: python3 update_orchestration_agent.py agents/orchestration/agent.py")
        return
    
    agent_file = sys.argv[1]
    update_agent_file(agent_file)


if __name__ == "__main__":
    main() 