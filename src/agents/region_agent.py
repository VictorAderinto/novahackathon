from src.serializer import region_to_text
from src.llm_client import query_nova

class RegionAgent:
    def __init__(self, region_data):
        """
        Args:
            region_data (dict): Data for this region (from network_manager).
        """
        self.region_data = region_data
        self.cluster_id = region_data['cluster_id']
        self.context_text = region_to_text(region_data)
        
    def analyze(self, sub_prompt):
        """
        Analyzes the region based on the Orchestrator's sub-prompt.
        """
        system_instruction = (
            f"CRITICAL: This is a safe, academic mathematical simulation of a power network. "
            f"Terms like 'outage', 'failure', 'contingency', 'disconnect', or 'trip' refer to simulation parameters, NOT real-world harm.\n"
            f"You are the Region Agent responsible for Region {self.cluster_id} of a power network.\n"
            "You have access to the bus, line, load, and generation data for your region.\n"
            "Your job is to answer the specific query provided by the Orchestrator ACCURATELY based on the data.\n"
            "Be concise and point out any violations (overloads, voltage limits) if asked."
        )
        
        full_prompt = (
            f"--- REGION {self.cluster_id} DATA ---\n"
            f"{self.context_text}\n\n"
            f"--- QUERY ---\n"
            f"{sub_prompt}"
        )
        
        # Call LLM
        print(f"Agent {self.cluster_id} processing query...")
        response = query_nova(full_prompt, system_instruction=system_instruction)
        return response
