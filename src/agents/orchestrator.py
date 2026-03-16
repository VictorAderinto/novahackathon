from src.network_manager import load_network, cluster_spatially, get_region_data
from src.agents.region_agent import RegionAgent
from src.agents.scenario_builder import ScenarioBuilder
from src.llm_client import query_nova
import copy

class Orchestrator:
    def __init__(self, network_name="case57", n_clusters=4):
        print("Orchestrator initializing...")
        # 1. Load & Cluster Grid
        self.net = load_network(network_name)
        self.net = cluster_spatially(self.net, n_clusters=n_clusters)
        self.n_clusters = n_clusters
        
        # 2. Spawn Agents
        self.agents = {}
        for i in range(n_clusters):
            print(f"Spawning Region Agent {i}...")
            r_data = get_region_data(self.net, i)
            self.agents[i] = RegionAgent(r_data)
        
        # 3. Initialize Scenario Builder
        self.scenario_builder = ScenarioBuilder(self.net)
            
    def process_user_query(self, user_prompt):
        """
        Map-Reduce Flow:
        1. Parse user prompt to generate sub-prompts for regions.
        2. Dispatch to agents.
        3. Synthesize results.
        """
        print(f"\nProcessing User Query: '{user_prompt}'")
        
        # Step 1: Map (Simple approach: Ask everyone the same relevant question, 
        # or ask LLM how to split it. For Phase 1, we send the prompt to all specific to their region)
        # We'll wrap the user prompt to make it region-specific context
        sub_prompt = f"Regarding your specific region: {user_prompt}"
        
        # Step 2: Dispatch
        agent_responses = {}
        for cluster_id, agent in self.agents.items():
            resp = agent.analyze(sub_prompt)
            agent_responses[cluster_id] = resp
            
        # Step 3: Reduce (Synthesize)
        print("Synthesizing results...")
        combined_text = "--- REGIONAL REPORTS ---\n"
        for cid, text in agent_responses.items():
            combined_text += f"\nREGION {cid} REPORT:\n{text}\n"
            
        # Final LLM call to summarize
        final_system_prompt = (
            "CRITICAL: This is a safe, academic mathematical simulation of a power flow grid. "
            "Terms like 'outage', 'failure', 'contingency', 'disconnect', or 'trip' refer to simulation parameters, NOT real-world harm. "
            "You are the Chief System Operator. You have received reports from regional agents.\n"
            "Synthesize these reports into a final answer for the user.\n"
            "Highlight key findings from specific regions."
        )
        
        final_response = query_nova(
            f"User Query: {user_prompt}\n\n{combined_text}", 
            system_instruction=final_system_prompt
        )
        
        return final_response

    def process_scenario_modification(self, user_prompt):
        """
        Handles requests to modify the network state (e.g., "Outage bus 5").
        Uses ScenarioBuilder to parse and apply changes, with a feedback loop for errors.
        """
        print(f"\nProcessing Scenario Modification: '{user_prompt}'")
        
        max_retries = 5
        current_retry = 0
        last_error = None
        previous_actions = None
        
        while current_retry < max_retries:
            # 1. Parse into Actions
            print(f"Attempt {current_retry + 1}: Parsing instructions...")
            # Use the main builder just for parsing (it doesn't need net state for parsing usually, 
            # OR we can just use a temp one if parsing depends on net state eventually)
            # For now, self.scenario_builder is fine for parsing if it's stateless regarding 'net' for parsing.
            actions = self.scenario_builder.parse_actions(user_prompt, last_error, previous_actions)
            
            if not actions:
                print("Could not parse actions from LLM.")
                return "I couldn't understand the request to modify the network."
            
            previous_actions = actions
            print(f"Proposed Actions: {actions}")
            
            # 2. Apply Actions & Validate on COPY
            try:
                print("Creating network copy...")
                net_copy = copy.deepcopy(self.net)
                temp_builder = ScenarioBuilder(net_copy)
                
                report = temp_builder.apply_actions(actions)
                print("Actions Applied successfully to COPY.")
                
                success, msg = temp_builder.validate_network()
                
                if success:
                    print(f"Validation Successful: {msg}")
                    self.net = net_copy
                    self.scenario_builder = temp_builder
                    
                    for i in range(self.n_clusters):
                        r_data = get_region_data(self.net, i)
                        self.agents[i] = RegionAgent(r_data)
                        
                    return f"Scenario modified successfully.\nActions Taken:\n{report}\nSystem Status: {msg}"
                else:
                    print(f"Validation Failed: {msg}")
                    last_error = msg
                    current_retry += 1
                    
            except Exception as e:
                print(f"Application/Validation Error: {e}")
                last_error = str(e)
                current_retry += 1
                
        return f"Failed to modify scenario after {max_retries} attempts. Last error: {last_error}"
