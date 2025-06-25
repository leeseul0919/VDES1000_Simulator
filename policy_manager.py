import json
class SentencePolicyManager:
    def __init__(self,policy_file):
        if policy_file:
            with open(policy_file, 'r') as file:
                self.policies = json.load(file)
        else:
            self.policies = {
                "EDM": {
                    "expected_responses":["EDO","EAK"], 
                    "structure": ["seq_nr","source_mmsi","dest_mmsi","data","fill_bits"],
                    "Field_conditions": {
                        "seq_nr": {"type":"int","range":[0,999],"is_null":False},
                        "source_mmsi": {"type":"int","range":[0,999999999],"is_null":True},
                        "dest_mmsi": {"type":"int","range":[0,999999999],"is_null":True},
                        "data": {"type":"str","range":[0,664],"is_null":False},
                        "fill_bits": {"type":"int","range":[0,6],"is_null":False}
                    },
                    "standard_v": "IALA G1139",
                    "requires_ack":["EAK"]
                },
                "OTHER": {"expected_responses": [], "structure":[], "Field_conditions": {},"standard_v": "","requires_ack":[]}
            }
        #print(self.policies)

    def get_policy(self,sentence_type):
        return self.policies.get(sentence_type,self.policies["OTHER"])
    
    def get_non_empty_responses(self):
        non_empty_responses = {}
        for key, policy in self.policies.items():
            if policy["expected_responses"]:
                non_empty_responses[key] = policy
                #print(non_empty_responses[key])
        return non_empty_responses
