from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.file_persistence import FilePersistence
from drain3.masking import MaskingInstruction
import os
import re

# Custom masking instructions to align with TRD
masking_instructions = [
    MaskingInstruction(r"((?<=[^A-Za-z0-9])|^)(([0-9a-f]{2,}:){3,}([0-9a-f]{2,}))((?=[^A-Za-z0-9])|$)", "<MAC>"),
    MaskingInstruction(r"((?<=[^A-Za-z0-9])|^)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})((?=[^A-Za-z0-9])|$)", "<IP>"),
    MaskingInstruction(r"((?<=[^A-Za-z0-9])|^)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})((?=[^A-Za-z0-9])|$)", "<UUID>"),
    MaskingInstruction(r"((?<=[^A-Za-z0-9])|^)(0x[a-fA-F0-9]+)((?=[^A-Za-z0-9])|$)", "<HEX>"),
    MaskingInstruction(r"((?<=[^A-Za-z0-9])|^)([\-\+]?\d+)((?=[^A-Za-z0-9])|$)", "<NUM>"),
    MaskingInstruction(r"(?i)((?<=[^A-Za-z0-9])|^)(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)((?=[^A-Za-z0-9])|$)", "<TIME>"),
]

class Drain3Manager:
    def __init__(self, state_dir: str = "/data/drain3-state"):
        self.state_dir = state_dir
        os.makedirs(self.state_dir, exist_ok=True)
        self.miners = {}

    def get_miner(self, source_id: str) -> TemplateMiner:
        if source_id not in self.miners:
            config = TemplateMinerConfig()
            config.load("") # Load default
            config.profiling_enabled = False
            config.drain_sim_th = 0.4
            config.drain_depth = 4
            config.drain_max_children = 100
            config.masking_instructions = masking_instructions
            
            persistence = FilePersistence(os.path.join(self.state_dir, f"{source_id}_state.bin"))
            miner = TemplateMiner(persistence_handler=persistence, config=config)
            self.miners[source_id] = miner
        return self.miners[source_id]

    def mine(self, source_id: str, log_message: str):
        miner = self.get_miner(source_id)
        result = miner.add_log_message(log_message)
        return result

    def extract(self, source_id: str, log_message: str):
        miner = self.get_miner(source_id)
        # Drain3 provides matching template and parameters
        cluster = miner.match(log_message)
        if not cluster:
            return None, None
            
        template = cluster.get_template()
        params = miner.extract_parameters(template, log_message)
        return template, params

drain3_manager = Drain3Manager()
