#!/usr/bin/env python3
"""
Script to update agent configuration to use localhost instead of hostnames
"""
import json
import os
import sys

def update_config(config_path):
    """
    Update agent configuration to use localhost instead of hostnames
    
    Args:
        config_path: Path to configuration file
    """
    if not os.path.exists(config_path):
        print(f"Error: Config file {config_path} not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Replace hostnames with localhost
        if "market_analysis_agent_url" in config:
            config["market_analysis_agent_url"] = config["market_analysis_agent_url"].replace("http://market-analysis-agent", "http://localhost")
        
        if "trade_execution_agent_url" in config:
            config["trade_execution_agent_url"] = config["trade_execution_agent_url"].replace("http://trade-execution-agent", "http://localhost")
        
        if "risk_management_agent_url" in config:
            config["risk_management_agent_url"] = config["risk_management_agent_url"].replace("http://risk-management-agent", "http://localhost")
        
        if "reporting_analytics_agent_url" in config:
            config["reporting_analytics_agent_url"] = config["reporting_analytics_agent_url"].replace("http://reporting-analytics-agent", "http://localhost")
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Updated configuration in {config_path}")
        return True
    
    except Exception as e:
        print(f"Error updating config: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 update_agent_config.py <config_file_path>")
        print("Example: python3 update_agent_config.py config/orchestration.json")
        return
    
    config_path = sys.argv[1]
    update_config(config_path)


if __name__ == "__main__":
    main() 