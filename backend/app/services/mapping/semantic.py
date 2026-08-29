import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple
from app.schemas.domain import CandidateField, MappingProposal
from app.services.schema_registry.core_schema import CORE_FIELDS

logger = logging.getLogger(__name__)

class SemanticMapper:
    def __init__(self):
        self.model = None
        self.core_embeddings = None
        self.core_names = [f["name"] for f in CORE_FIELDS]
        self.core_types = {f["name"]: f["type"] for f in CORE_FIELDS}
        
    def _load_model(self):
        if self.model is None:
            logger.info("Loading sentence transformer model for semantic mapping...")
            # all-MiniLM-L6-v2 is small and fast for CPU
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Precompute core field embeddings
            descriptions = [f"{f['name']} : {f['description']}" for f in CORE_FIELDS]
            self.core_embeddings = self.model.encode(descriptions, convert_to_numpy=True)
            
    def compute_similarity(self, candidate_context: str) -> np.ndarray:
        self._load_model()
        cand_emb = self.model.encode([candidate_context], convert_to_numpy=True)
        # Cosine similarity
        similarities = np.dot(self.core_embeddings, cand_emb.T).flatten()
        norms = np.linalg.norm(self.core_embeddings, axis=1) * np.linalg.norm(cand_emb)
        similarities = similarities / (norms + 1e-9)
        return similarities

    def evaluate_type_agreement(self, inferred_type: str, target_type: str) -> float:
        if not inferred_type or inferred_type == "text":
            return 0.5 # Neutral
            
        if inferred_type == target_type:
            return 1.0
            
        # Hard gate
        return 0.0

    def propose_mappings(self, candidate: CandidateField, template_pattern: str) -> List[MappingProposal]:
        # Context is the field key, and its inferred type
        context_str = f"field {candidate.field_key} type {candidate.inferred_type} in {template_pattern}"
        sims = self.compute_similarity(context_str)
        
        proposals = []
        for i, target_name in enumerate(self.core_names):
            s_name = float(sims[i])
            # Normalize s_name to 0-1 (cosine sim is -1 to 1)
            s_name = max(0.0, s_name)
            
            s_value = self.evaluate_type_agreement(candidate.inferred_type, self.core_types[target_name])
            s_context = 0.5 # Heuristic, could be improved
            s_history = 0.0 # Heuristic, could pull from DB
            
            # C = 0.35 * S_name + 0.30 * S_value + 0.20 * S_context + 0.15 * S_history
            c = 0.35 * s_name + 0.30 * s_value + 0.20 * s_context + 0.15 * s_history
            
            if s_value == 0.0:
                c = min(c, 0.50)
                
            decision = "extension_only"
            if c >= 0.90:
                decision = "auto_accepted"
            elif c >= 0.65:
                decision = "review"
                
            proposals.append(MappingProposal(
                source_field=candidate.field_key,
                target_field=target_name,
                confidence=c,
                decision=decision,
                signals={
                    "name": s_name,
                    "value": s_value,
                    "context": s_context,
                    "history": s_history
                }
            ))
            
        # Sort by confidence
        proposals.sort(key=lambda x: x.confidence, reverse=True)
        return proposals

semantic_mapper = SemanticMapper()
