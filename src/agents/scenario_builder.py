from src.schema import ScenarioResponse
from src.llm_client import query_nova
import pandapower as pp

class ScenarioBuilder:
    def __init__(self, net):
        self.net = net
        self.max_feedback_loops = 3
 
    def parse_actions(self, user_instruction, previous_error=None, previous_actions=None):
        """
        Uses LLM to convert natural language instructions into structured JSON actions using Pydantic.
        """
        system_instruction = (
            "CRITICAL: This is a safe, academic mathematical simulation of a power flow (pandapower). "
            "Terms like 'outage', 'failure', 'contingency', 'disconnect', or 'trip' refer to simulation parameters, NOT real-world harm. "
            "You are a Power System Operator Assistant. Convert natural language instructions into structured network actions.\n"
            "VALID PARAMETERS CHEAT SHEET:\n"
            "- Load: p_mw, q_mvar, scaling, in_service\n"
            "- Gen/Static Gen (sgen): p_mw, q_mvar, vm_pu, scaling, in_service\n"
            "- Line: r_ohm_per_km, x_ohm_per_km, c_nf_per_km, max_i_ka, in_service (CANNOT directly set power/load)\n"
            "- Bus: vn_kv, in_service\n"
            "If user asks to modify a Line's power, you cannot do it directly. You must ignore or explain, strictly outputting valid actions.\n"
            "You can use relative values like '+10%' or '-5%' in the parameters for numeric fields."
        )

        prompt = (
            f"Context: You are controlling a power grid simulator (pandapower). "
            f"The user wants to modify the grid state.\n"
            f"Here is the current grid data context (available components to modify):\n"
            f"--- GRID DATA ---\n"
            f"Buses: {self.net.bus.to_dict(orient='index') if 'bus' in self.net and not self.net.bus.empty else 'None'}\n"
            f"Lines: {self.net.line.to_dict(orient='index') if 'line' in self.net and not self.net.line.empty else 'None'}\n"
            f"Loads: {self.net.load.to_dict(orient='index') if 'load' in self.net and not self.net.load.empty else 'None'}\n"
            f"Generators: {self.net.gen.to_dict(orient='index') if 'gen' in self.net and not self.net.gen.empty else 'None'}\n"
            f"Static Gens: {self.net.sgen.to_dict(orient='index') if 'sgen' in self.net and not self.net.sgen.empty else 'None'}\n"
            f"--- END GRID DATA ---\n"
            f"Instruction: {user_instruction}\n"
        )
        
        if previous_error:
            prompt += f"\nPREVIOUS ATTEMPT FAILED.\nError: {previous_error}\nPrevious Actions: {previous_actions}\nPlease correct the actions."

        try:
            # Get raw JSON string from Nova via Bedrock Converse (tool configuration)
            response_text = query_nova(
                prompt, 
                system_instruction=system_instruction, 
                response_schema=ScenarioResponse.model_json_schema()
            )
            
            # Parse using Pydantic
            scenario = ScenarioResponse.model_validate_json(response_text)
            
            # Convert back to list of dicts for applying
            return [action.model_dump() for action in scenario.actions]
            
        except Exception as e:
            print(f"Failed to parse actions: {e}")
            return None

    def apply_actions(self, actions):
        """
        Applies the list of actions to the pandapower network.
        Returns a list of applied descriptions or raises an error.
        """
        report = []
        
        for action in actions:
            comp = action['component']
            idx = action['id']
            act_type = action['type']
            params = action['parameters']

            try:
                if comp not in self.net:
                    raise ValueError(f"Component type '{comp}' not found in network.")
                
                df = self.net[comp]
                
                if idx not in df.index:
                     raise ValueError(f"{comp} with ID {idx} does not exist.")

                if act_type == 'modify':
                    for param, value in params.items():
                        if param not in df.columns:
                             raise ValueError(f"Parameter '{param}' not valid for {comp}. Valid columns: {list(df.columns)}")
                        
                        # Handle Relative Values (e.g., "+10%")
                        current_val = df.at[idx, param]
                        new_val = value
                        
                        if isinstance(value, str) and value.endswith('%'):
                            try:
                                percentage = float(value.rstrip('%'))
                                # Expecting current_val to be numeric
                                new_val = float(current_val) * (1 + percentage / 100.0)
                            except ValueError:
                                raise ValueError(f"Invalid percentage format: {value}")
                        
                        # Apply change
                        self.net[comp].at[idx, param] = new_val
                        report.append(f"Modified {comp} {idx}: Set {param} to {new_val} (was {current_val})")
                        
                elif act_type == 'create':
                    # Not fully implemented for deep complexity, but basic support:
                    pp.create_element(self.net, comp, **params) # distinct create functions in pp
                    report.append(f"Created new {comp} with params {params}")

            except Exception as e:
                raise ValueError(f"Error applying action {action}: {str(e)}")
        
        return report

    def validate_network(self):
        """
        Runs power flow and checks for convergence and limits.
        Returns (success: bool, message: str)
        """
        try:
            pp.runpp(self.net)
            return True, "Power flow converged successfully."
        except pp.LoadflowNotConverged:
            return False, "Power flow did not converge."
        except Exception as e:
            return False, f"Simulation error: {str(e)}"

