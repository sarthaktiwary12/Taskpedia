"""
Task Ontology Schema for PRAXIS.

Defines the canonical structure for task definitions following the Dictionary Model:
- One file = One cultural task
- Precondition / Postcondition / Invariants structure
- Language-first, alphabetical sharding
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GenerationMethod(str, Enum):
    """Method used to generate a task."""

    SEED_EXTRACTED = "seed_extracted"
    VERB_NOUN_MATRIX = "verb_noun_matrix"
    LLM_DECOMPOSITION = "llm_decomposition"
    LLM_EXPANSION = "llm_expansion"
    CULTURAL_ADAPTATION = "cultural_adaptation"
    HUMAN_CURATED = "human_curated"
    EVOLVED = "evolved"


class VerificationStatus(str, Enum):
    """Verification status of a task."""

    UNVERIFIED = "unverified"
    LLM_VALIDATED = "llm_validated"
    HUMAN_VALIDATED = "human_validated"
    REJECTED = "rejected"


@dataclass
class CompletionCriteria:
    """The defining element of a task - structured textual completion."""

    precondition: str  # State of the world before starting
    postcondition: str  # State of the world that signifies success
    invariants: str  # Constraints that must be maintained throughout

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "precondition": self.precondition,
            "postcondition": self.postcondition,
            "invariants": self.invariants,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompletionCriteria:
        """Create from dictionary."""
        return cls(
            precondition=data.get("precondition", ""),
            postcondition=data.get("postcondition", ""),
            invariants=data.get("invariants", ""),
        )


@dataclass
class Relationships:
    """Graph structure connecting tasks."""

    part_of: list[str] = field(default_factory=list)
    composed_of: list[str] = field(default_factory=list)
    requires_ability: list[str] = field(default_factory=list)
    similar: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary."""
        return {
            "part_of": self.part_of,
            "composed_of": self.composed_of,
            "requires_ability": self.requires_ability,
            "similar": self.similar,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Relationships:
        """Create from dictionary."""
        return cls(
            part_of=data.get("part_of", []),
            composed_of=data.get("composed_of", []),
            requires_ability=data.get("requires_ability", []),
            similar=data.get("similar", []),
        )


@dataclass
class Provenance:
    """Origin and verification metadata."""

    sources: list[str] = field(default_factory=list)
    generation_method: GenerationMethod = GenerationMethod.LLM_EXPANSION
    generation_prompt_hash: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence_score: float = 0.5
    generation_timestamp: str | None = None
    parent_task_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sources": self.sources,
            "generation_method": self.generation_method.value,
            "generation_prompt_hash": self.generation_prompt_hash,
            "verification_status": self.verification_status.value,
            "confidence_score": self.confidence_score,
            "generation_timestamp": self.generation_timestamp,
            "parent_task_id": self.parent_task_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Provenance:
        """Create from dictionary."""
        return cls(
            sources=data.get("sources", []),
            generation_method=GenerationMethod(
                data.get("generation_method", "llm_expansion")
            ),
            generation_prompt_hash=data.get("generation_prompt_hash"),
            verification_status=VerificationStatus(
                data.get("verification_status", "unverified")
            ),
            confidence_score=data.get("confidence_score", 0.5),
            generation_timestamp=data.get("generation_timestamp"),
            parent_task_id=data.get("parent_task_id"),
        )


@dataclass
class Task:
    """
    A single cultural task definition.

    ID format: {language}_{normalized_name}
    File path: /tasks/{language}/{first_char}/{name}.yaml
    """

    id: str
    name: str
    language: str
    region: str | None = None

    aliases: list[str] = field(default_factory=list)
    concept: str | None = None
    related_cultural_variants: list[str] = field(default_factory=list)

    # THE CORE
    completion: CompletionCriteria = field(
        default_factory=lambda: CompletionCriteria("", "", "")
    )

    # Graph structure
    relationships: Relationships = field(default_factory=Relationships)

    # Prose descriptions
    physical: str = ""
    sensing: str = ""
    cognitive: str = ""
    context: str = ""

    # Factual, filterable properties
    tags: list[str] = field(default_factory=list)

    # Metadata
    provenance: Provenance = field(default_factory=Provenance)

    # Quality metrics
    quality_scores: dict[str, float] = field(default_factory=dict)

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize task name for ID and filename."""
        normalized = name.lower().strip()
        normalized = re.sub(r"\s+", "_", normalized)
        normalized = re.sub(r"[^\w\u0080-\uffff]", "", normalized)
        return normalized

    @staticmethod
    def generate_id(language: str, name: str) -> str:
        """Generate canonical task ID."""
        return f"{language}_{Task.normalize_name(name)}"

    def get_file_path(self) -> str:
        """Get the canonical file path for this task."""
        normalized = Task.normalize_name(self.name)
        first_char = normalized[0] if normalized else "_"
        return f"/tasks/{self.language}/{first_char}/{normalized}.yaml"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "region": self.region,
            "aliases": self.aliases,
            "concept": self.concept,
            "related_cultural_variants": self.related_cultural_variants,
            "completion": self.completion.to_dict(),
            "relationships": self.relationships.to_dict(),
            "physical": self.physical,
            "sensing": self.sensing,
            "cognitive": self.cognitive,
            "context": self.context,
            "tags": self.tags,
            "provenance": self.provenance.to_dict(),
            "quality_scores": self.quality_scores,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Create Task from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            language=data["language"],
            region=data.get("region"),
            aliases=data.get("aliases", []),
            concept=data.get("concept"),
            related_cultural_variants=data.get("related_cultural_variants", []),
            completion=CompletionCriteria.from_dict(data.get("completion", {})),
            relationships=Relationships.from_dict(data.get("relationships", {})),
            physical=data.get("physical", ""),
            sensing=data.get("sensing", ""),
            cognitive=data.get("cognitive", ""),
            context=data.get("context", ""),
            tags=data.get("tags", []),
            provenance=Provenance.from_dict(data.get("provenance", {})),
            quality_scores=data.get("quality_scores", {}),
        )


# Canonical tag vocabulary
CANONICAL_TAGS = {
    # Manipulation
    "unimanual", "bimanual", "fine_motor", "gross_motor", "precision_required",
    "high_force", "low_force", "tool_required", "tool_free",
    # Locomotion
    "stationary", "locomotion_required", "walking", "running", "climbing",
    "crawling", "jumping", "balancing",
    # Object properties
    "fragile_object", "heavy_object", "flexible_object", "liquid", "granular",
    "hot", "cold", "sharp", "electrical",
    # Environment
    "indoor", "outdoor", "either_environment",
    "kitchen", "bathroom", "bedroom", "office", "workshop", "vehicle",
    # Timing
    "quick", "extended", "ongoing", "periodic", "time_critical",
    # Social
    "solo", "cooperative", "communicative", "language_involved",
    # Safety
    "safety_critical", "reversible", "irreversible",
    # Cognitive
    "planning_required", "realtime_reactive", "memory_required",
    "decision_making", "creativity_required",
    # Domain hints
    "food_preparation", "cleaning", "maintenance", "medical",
    "childcare", "eldercare", "transportation", "communication",
}


# Supported languages (~30)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "Chinese (Mandarin)",
    "es": "Spanish",
    "hi": "Hindi",
    "ar": "Arabic",
    "pt": "Portuguese",
    "bn": "Bengali",
    "ru": "Russian",
    "ja": "Japanese",
    "pa": "Punjabi",
    "de": "German",
    "jv": "Javanese",
    "ko": "Korean",
    "fr": "French",
    "te": "Telugu",
    "mr": "Marathi",
    "tr": "Turkish",
    "ta": "Tamil",
    "vi": "Vietnamese",
    "it": "Italian",
    "th": "Thai",
    "fa": "Persian",
    "pl": "Polish",
    "uk": "Ukrainian",
    "nl": "Dutch",
    "id": "Indonesian",
    "ms": "Malay",
    "sw": "Swahili",
    "he": "Hebrew",
    "el": "Greek",
}
