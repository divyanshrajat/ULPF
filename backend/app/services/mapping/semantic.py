import logging
import os
import numpy as np
from typing import List, Optional
from app.schemas.domain import CandidateField, MappingProposal
from app.services.schema_registry.core_schema import CORE_FIELDS

logger = logging.getLogger(__name__)

MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"


class SemanticMapper:
    def __init__(self):
        self.model = None
        self.core_embeddings = None
        self.core_names = [f["name"] for f in CORE_FIELDS]
        self.core_types = {f["name"]: f["type"] for f in CORE_FIELDS}
        self._load_failed = False

    def _load_model(self):
        """
        Load the local SentenceTransformer model.
        - In airgap mode: only loads from a local path. Never downloads.
        - In internet mode: falls back to model name (may download on first use).
        - If model is unavailable, sets _load_failed=True and returns gracefully.
        """
        if self.model is not None or self._load_failed:
            return

        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import settings

            model_path = settings.ULPF_MODEL_PATH

            if settings.ULPF_MODE == "airgap":
                # Strict: must be a local path that exists
                if not os.path.isabs(model_path) or not os.path.isdir(model_path):
                    logger.error(
                        f"AIR-GAP MODE: Model not found at '{model_path}'. "
                        f"Set ULPF_MODEL_PATH to a pre-downloaded model directory."
                    )
                    self._load_failed = True
                    return

            logger.info(f"Loading SentenceTransformer model from '{model_path}'...")
            self.model = SentenceTransformer(model_path)

            descriptions = [f"{f['name']} : {f['description']}" for f in CORE_FIELDS]
            self.core_embeddings = self.model.encode(descriptions, convert_to_numpy=True)
            logger.info("Semantic model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load semantic model: {e}")
            self._load_failed = True

    def compute_similarity(self, candidate_context: str) -> np.ndarray:
        """Return semantic similarity scores. Returns zero-array if model unavailable."""
        self._load_model()
        if self._load_failed or self.model is None:
            # Return neutral zeros — mapping will fall back to deterministic signals only
            return np.zeros(len(self.core_names))

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

    def propose_mappings(self, db, source_id: str, template_id: str, candidate: CandidateField, template_pattern: str) -> List[MappingProposal]:
        from app.models.domain import Mapping
        
        # Context is the field key, and its inferred type
        context_str = f"field {candidate.field_key} type {candidate.inferred_type} in {template_pattern}"
        sims = self.compute_similarity(context_str)
        
        # Fetch history from DB for all active mappings to learn across sources
        history_mappings = db.query(Mapping).filter(Mapping.status == "active").all()
        historical_targets = {}
        for m in history_mappings:
            for k, v in m.field_bindings.items():
                if k == candidate.field_key:
                    historical_targets[v] = historical_targets.get(v, 0) + 1
        
        proposals = []
        for i, target_name in enumerate(self.core_names):
            s_name = float(sims[i])
            s_name = max(0.0, s_name)
            
            s_value = self.evaluate_type_agreement(candidate.inferred_type, self.core_types[target_name])
            
            # Context: if the pattern contains words related to the target
            target_group = target_name.split('.')[0] if '.' in target_name else target_name
            s_context = 0.8 if target_group.lower() in template_pattern.lower() else 0.4
            
            # History: how many times was this exact field mapped to this target?
            hist_count = historical_targets.get(target_name, 0)
            s_history = min(1.0, hist_count * 0.5)
            
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
                    "name": round(s_name, 3),
                    "value": round(s_value, 3),
                    "context": round(s_context, 3),
                    "history": round(s_history, 3)
                }
            ))
            
        proposals.sort(key=lambda x: x.confidence, reverse=True)
        return proposals

semantic_mapper = SemanticMapper()
