"""
Task Ontology Schema

Defines the canonical structure for task definitions following the Dictionary Model:
- One file = One cultural task
- Precondition / Postcondition / Invariants structure
- Language-first, alphabetical sharding
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import hashlib
import json
import re


class GenerationMethod(str, Enum):
    SEED_EXTRACTED = "seed_extracted"           # From existing datasets
    VERB_NOUN_MATRIX = "verb_noun_matrix"       # Systematic generation
    LLM_DECOMPOSITION = "llm_decomposition"     # Recursive subtask breakdown
    LLM_EXPANSION = "llm_expansion"             # Horizontal expansion
    CULTURAL_ADAPTATION = "cultural_adaptation"  # Cross-cultural variant
    HUMAN_CURATED = "human_curated"             # Manual entry
    EVOLVED = "evolved"                         # Evol-Instruct style mutation


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    LLM_VALIDATED = "llm_validated"
    HUMAN_VALIDATED = "human_validated"
    REJECTED = "rejected"


@dataclass
class CompletionCriteria:
    """The defining element of a task - structured textual completion."""
    precondition: str      # State of the world before starting
    postcondition: str     # State of the world that signifies success
    invariants: str        # Constraints that must be maintained throughout


@dataclass
class Relationships:
    """Graph structure connecting tasks."""
    part_of: list[str] = field(default_factory=list)          # Parent tasks this is a subtask of
    composed_of: list[str] = field(default_factory=list)      # Child subtasks
    requires_ability: list[str] = field(default_factory=list) # Prerequisite capabilities
    similar: list[str] = field(default_factory=list)          # Related tasks for transfer


@dataclass
class Provenance:
    """Origin and verification metadata."""
    sources: list[str] = field(default_factory=list)
    generation_method: GenerationMethod = GenerationMethod.LLM_EXPANSION
    generation_prompt_hash: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence_score: float = 0.5  # 0-1, from LLM-as-judge
    generation_timestamp: Optional[str] = None
    parent_task_id: Optional[str] = None  # For decomposed tasks


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
    region: Optional[str] = None
    
    aliases: list[str] = field(default_factory=list)
    
    # Loose conceptual grouping (not hierarchy)
    concept: Optional[str] = None
    related_cultural_variants: list[str] = field(default_factory=list)
    
    # THE CORE
    completion: CompletionCriteria = field(default_factory=lambda: CompletionCriteria("", "", ""))
    
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
    
    # Quality metrics (filled during validation)
    quality_scores: dict = field(default_factory=dict)
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize task name for ID and filename."""
        # Lowercase, replace spaces with underscores, remove special chars
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', '_', normalized)
        normalized = re.sub(r'[^\w\u0080-\uffff]', '', normalized)  # Keep unicode letters
        return normalized
    
    @staticmethod
    def generate_id(language: str, name: str) -> str:
        """Generate canonical task ID."""
        return f"{language}_{Task.normalize_name(name)}"
    
    def get_file_path(self) -> str:
        """Get the canonical file path for this task."""
        normalized = Task.normalize_name(self.name)
        first_char = normalized[0] if normalized else '_'
        return f"/tasks/{self.language}/{first_char}/{normalized}.yaml"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'language': self.language,
            'region': self.region,
            'aliases': self.aliases,
            'concept': self.concept,
            'related_cultural_variants': self.related_cultural_variants,
            'completion': {
                'precondition': self.completion.precondition,
                'postcondition': self.completion.postcondition,
                'invariants': self.completion.invariants,
            },
            'relationships': {
                'part_of': self.relationships.part_of,
                'composed_of': self.relationships.composed_of,
                'requires_ability': self.relationships.requires_ability,
                'similar': self.relationships.similar,
            },
            'physical': self.physical,
            'sensing': self.sensing,
            'cognitive': self.cognitive,
            'context': self.context,
            'tags': self.tags,
            'provenance': {
                'sources': self.provenance.sources,
                'generation_method': self.provenance.generation_method.value,
                'generation_prompt_hash': self.provenance.generation_prompt_hash,
                'verification_status': self.provenance.verification_status.value,
                'confidence_score': self.provenance.confidence_score,
                'generation_timestamp': self.provenance.generation_timestamp,
                'parent_task_id': self.provenance.parent_task_id,
            },
            'quality_scores': self.quality_scores,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Create Task from dictionary."""
        completion = CompletionCriteria(
            precondition=data.get('completion', {}).get('precondition', ''),
            postcondition=data.get('completion', {}).get('postcondition', ''),
            invariants=data.get('completion', {}).get('invariants', ''),
        )
        
        relationships = Relationships(
            part_of=data.get('relationships', {}).get('part_of', []),
            composed_of=data.get('relationships', {}).get('composed_of', []),
            requires_ability=data.get('relationships', {}).get('requires_ability', []),
            similar=data.get('relationships', {}).get('similar', []),
        )
        
        prov_data = data.get('provenance', {})
        provenance = Provenance(
            sources=prov_data.get('sources', []),
            generation_method=GenerationMethod(prov_data.get('generation_method', 'llm_expansion')),
            generation_prompt_hash=prov_data.get('generation_prompt_hash'),
            verification_status=VerificationStatus(prov_data.get('verification_status', 'unverified')),
            confidence_score=prov_data.get('confidence_score', 0.5),
            generation_timestamp=prov_data.get('generation_timestamp'),
            parent_task_id=prov_data.get('parent_task_id'),
        )
        
        return cls(
            id=data['id'],
            name=data['name'],
            language=data['language'],
            region=data.get('region'),
            aliases=data.get('aliases', []),
            concept=data.get('concept'),
            related_cultural_variants=data.get('related_cultural_variants', []),
            completion=completion,
            relationships=relationships,
            physical=data.get('physical', ''),
            sensing=data.get('sensing', ''),
            cognitive=data.get('cognitive', ''),
            context=data.get('context', ''),
            tags=data.get('tags', []),
            provenance=provenance,
            quality_scores=data.get('quality_scores', {}),
        )


# Canonical tag vocabulary (factual, filterable properties)
CANONICAL_TAGS = {
    # Manipulation
    'unimanual', 'bimanual', 'fine_motor', 'gross_motor', 'precision_required',
    'high_force', 'low_force', 'tool_required', 'tool_free',
    
    # Locomotion
    'stationary', 'locomotion_required', 'walking', 'running', 'climbing',
    'crawling', 'jumping', 'balancing',
    
    # Object properties
    'fragile_object', 'heavy_object', 'flexible_object', 'liquid', 'granular',
    'hot', 'cold', 'sharp', 'electrical',
    
    # Environment
    'indoor', 'outdoor', 'either_environment',
    'kitchen', 'bathroom', 'bedroom', 'office', 'workshop', 'vehicle',
    
    # Timing
    'quick', 'extended', 'ongoing', 'periodic', 'time_critical',
    
    # Social
    'solo', 'cooperative', 'communicative', 'language_involved',
    
    # Safety
    'safety_critical', 'reversible', 'irreversible',
    
    # Cognitive
    'planning_required', 'realtime_reactive', 'memory_required',
    'decision_making', 'creativity_required',
    
    # Domain hints (objective, not categorical)
    'food_preparation', 'cleaning', 'maintenance', 'medical',
    'childcare', 'eldercare', 'transportation', 'communication',
}


# Supported languages (mirroring LLM coverage, ~30)
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'zh': 'Chinese (Mandarin)',
    'es': 'Spanish',
    'hi': 'Hindi',
    'ar': 'Arabic',
    'pt': 'Portuguese',
    'bn': 'Bengali',
    'ru': 'Russian',
    'ja': 'Japanese',
    'pa': 'Punjabi',
    'de': 'German',
    'jv': 'Javanese',
    'ko': 'Korean',
    'fr': 'French',
    'te': 'Telugu',
    'mr': 'Marathi',
    'tr': 'Turkish',
    'ta': 'Tamil',
    'vi': 'Vietnamese',
    'it': 'Italian',
    'th': 'Thai',
    'fa': 'Persian',
    'pl': 'Polish',
    'uk': 'Ukrainian',
    'nl': 'Dutch',
    'id': 'Indonesian',
    'ms': 'Malay',
    'sw': 'Swahili',
    'he': 'Hebrew',
    'el': 'Greek',
}
