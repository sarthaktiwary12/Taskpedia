"""
Task Generator

Core generation logic including:
- Verb-noun matrix generation
- LLM-based task generation with structured prompts
- Self-consistency validation
- Evol-Instruct style evolution
- Persona-based generation for diversity
"""

import json
import hashlib
import random
from datetime import datetime
from typing import Optional, Generator
from dataclasses import dataclass

from schema import (
    Task, CompletionCriteria, Relationships, Provenance,
    GenerationMethod, VerificationStatus, CANONICAL_TAGS
)
from seeds import VerbEntry, NounEntry, get_seed_verbs, get_seed_nouns
from config import GenerationConfig, LLMConfig


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

TASK_GENERATION_PROMPT = """You are creating entries for a comprehensive dictionary of human tasks. Each task must be precisely defined with clear completion criteria.

Generate a task definition for: {task_phrase}
Language: {language}
Cultural context: {cultural_context}

Respond with a JSON object following this exact structure:
{{
    "name": "the task name in {language}",
    "aliases": ["alternative names for this task"],
    "concept": "universal concept this belongs to (e.g., 'food_preparation', 'greeting', 'cleaning')",
    "completion": {{
        "precondition": "State of the world before starting. What must be true? What is available?",
        "postcondition": "State of the world that signifies success. What has changed?",
        "invariants": "Constraints that must be maintained throughout. What must NOT happen?"
    }},
    "physical": "Description of physical actions involved. Body parts used, forces applied, movements required. Write 'None - purely cognitive task' if not applicable.",
    "sensing": "Sensory requirements. What must be perceived? Visual, tactile, auditory, proprioceptive needs.",
    "cognitive": "Mental requirements. Planning, decision-making, memory, attention needed.",
    "context": "Typical environment and situation. Where and when does this usually happen?",
    "tags": ["list", "of", "relevant", "tags"],
    "composed_of": ["subtask1", "subtask2"],
    "requires_ability": ["prerequisite_skill1", "prerequisite_skill2"],
    "is_valid_task": true,
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this is or isn't a valid human task"
}}

Valid tags include: {valid_tags}

Important:
- Completion criteria must be specific enough to verify success/failure
- If this verb-noun combination doesn't make sense as a human task, set is_valid_task to false
- Be culturally specific where relevant
- Physical/sensing/cognitive should be prose descriptions, not lists"""


TASK_DECOMPOSITION_PROMPT = """You are decomposing a task into its constituent subtasks for a comprehensive task dictionary.

Parent task: {task_name}
Completion criteria:
- Precondition: {precondition}
- Postcondition: {postcondition}
- Invariants: {invariants}

Physical description: {physical}

Decompose this into {min_subtasks} to {max_subtasks} sequential or parallel subtasks.
Each subtask must:
1. Have its own clear completion criteria
2. Be more atomic than the parent
3. Together, completing all subtasks should complete the parent task

Respond with a JSON array:
[
    {{
        "name": "subtask name",
        "sequence_order": 1,
        "is_parallel": false,
        "completion": {{
            "precondition": "...",
            "postcondition": "...",
            "invariants": "..."
        }},
        "physical": "...",
        "sensing": "...",
        "cognitive": "...",
        "tags": ["..."],
        "is_atomic": false
    }},
    ...
]

Set is_atomic to true if the subtask cannot be meaningfully decomposed further."""


TASK_EXPANSION_PROMPT = """You are expanding the task dictionary by finding similar or related tasks.

Given task: {task_name}
Description: {task_description}
Tags: {tags}

Generate {num_similar} similar but distinct tasks that:
1. Share some characteristics but are clearly different
2. Might transfer learning from this task
3. Cover variations in context, tools, or objects

Respond with a JSON array:
[
    {{
        "name": "similar task name",
        "relationship": "similar" | "variation" | "related_skill",
        "difference": "how it differs from the original",
        "shared_skills": ["skills that transfer"]
    }},
    ...
]"""


TASK_EVOLUTION_PROMPT = """You are evolving a task to create more diverse training examples.

Original task: {task_name}
Completion:
- Precondition: {precondition}
- Postcondition: {postcondition}

Mutation type: {mutation_type}

Apply the mutation to create a new, valid task variant:
- add_constraint: Make the task more specific or challenging
- remove_constraint: Make the task more general
- change_context: Move to a different environment
- add_tool: Require use of a specific tool
- remove_tool: Do without a tool typically used
- add_person: Make it collaborative
- time_pressure: Add urgency
- precision_increase: Require more accuracy

Respond with JSON:
{{
    "name": "evolved task name",
    "mutation_applied": "description of what changed",
    "completion": {{
        "precondition": "...",
        "postcondition": "...",
        "invariants": "..."
    }},
    "physical": "...",
    "sensing": "...",
    "cognitive": "...",
    "tags": ["..."],
    "difficulty_change": "easier" | "same" | "harder"
}}"""


CULTURAL_ADAPTATION_PROMPT = """You are adapting a task for a specific cultural context.

Original task (English): {original_task}
Original completion criteria:
- Precondition: {precondition}
- Postcondition: {postcondition}

Target language: {target_language}
Target culture/region: {target_culture}

Create the culturally appropriate version of this task. This is NOT just translation - consider:
1. Different tools, materials, or methods used in this culture
2. Different social norms or expectations
3. Different environments or contexts
4. Whether this task even exists in this culture

Respond with JSON:
{{
    "name": "task name in target language",
    "name_romanized": "romanization if non-Latin script",
    "is_culturally_relevant": true,
    "cultural_notes": "how this differs from the original",
    "completion": {{
        "precondition": "...",
        "postcondition": "...",
        "invariants": "..."
    }},
    "physical": "...",
    "sensing": "...",
    "cognitive": "...",
    "context": "...",
    "tags": ["..."]
}}

If this task doesn't exist or is very rare in the target culture, set is_culturally_relevant to false."""


VALIDITY_CHECK_PROMPT = """You are validating a task definition for a comprehensive task dictionary.

Task: {task_name}
Completion criteria:
- Precondition: {precondition}
- Postcondition: {postcondition}
- Invariants: {invariants}

Evaluate this task on the following criteria (score 0.0 to 1.0):

1. completion_clarity: Can success/failure be objectively determined from the postcondition?
2. precondition_completeness: Are all necessary starting conditions specified?
3. postcondition_specificity: Is the end state unambiguous?
4. invariant_necessity: Are the invariants meaningful and necessary?
5. physical_accuracy: Does the physical description match the task? (N/A for cognitive tasks)
6. tag_accuracy: Are the tags appropriate?
7. is_real_task: Is this something humans actually do?

Respond with JSON:
{{
    "scores": {{
        "completion_clarity": 0.0-1.0,
        "precondition_completeness": 0.0-1.0,
        "postcondition_specificity": 0.0-1.0,
        "invariant_necessity": 0.0-1.0,
        "physical_accuracy": 0.0-1.0,
        "tag_accuracy": 0.0-1.0,
        "is_real_task": 0.0-1.0
    }},
    "overall_score": 0.0-1.0,
    "issues": ["list of specific problems found"],
    "suggestions": ["list of improvements"]
}}"""


PERSONA_PROMPTS = {
    "occupational_therapist": "You are an occupational therapist focused on activities of daily living and rehabilitation. Consider task accessibility, adaptive techniques, and therapeutic value.",
    "chef": "You are a professional chef. Focus on culinary tasks, kitchen techniques, food safety, and mise en place.",
    "nurse": "You are a registered nurse. Consider medical tasks, patient care, safety protocols, and healthcare procedures.",
    "construction_worker": "You are a construction worker. Focus on building tasks, tool use, physical safety, and material handling.",
    "office_worker": "You are an office professional. Consider administrative tasks, computer use, communication, and organization.",
    "parent": "You are a parent of young children. Focus on childcare, household management, safety, and nurturing tasks.",
    "athlete": "You are a professional athlete. Consider physical training, sports techniques, body mechanics, and performance.",
    "artist": "You are a visual artist. Focus on creative tasks, artistic techniques, materials, and aesthetic considerations.",
    "engineer": "You are an engineer. Consider technical tasks, precision, problem-solving, and systematic approaches.",
    "elder": "You are an elderly person. Focus on task accessibility, energy conservation, and safety considerations.",
}


# =============================================================================
# GENERATOR CLASS
# =============================================================================

@dataclass
class GenerationResult:
    """Result of a generation attempt."""
    task: Optional[Task]
    success: bool
    error: Optional[str] = None
    raw_response: Optional[str] = None
    prompt_hash: Optional[str] = None


class TaskGenerator:
    """
    Main task generator implementing SOTA synthetic data techniques.
    """
    
    def __init__(self, config: GenerationConfig, llm_config: LLMConfig):
        self.config = config
        self.llm_config = llm_config
        self.generated_count = 0
        self.failed_count = 0
        
        # For deduplication during generation
        self.seen_task_names: set[str] = set()
        self.seen_task_hashes: set[str] = set()
    
    def _hash_prompt(self, prompt: str) -> str:
        """Generate hash of prompt for provenance tracking."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"
    
    def _call_llm(self, prompt: str, temperature: Optional[float] = None) -> Optional[dict]:
        """
        Call LLM and parse JSON response.
        
        In production, this would call the actual API.
        For now, returns a placeholder structure.
        """
        # This is where you'd integrate with Claude API
        # For now, we'll create a mock response structure
        
        # In production:
        # response = anthropic.messages.create(
        #     model=self.llm_config.model,
        #     max_tokens=self.llm_config.max_tokens,
        #     temperature=temperature or self.llm_config.temperature,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return json.loads(response.content[0].text)
        
        return None  # Placeholder - implement with actual API
    
    def _parse_task_response(self, response: dict, language: str, 
                             generation_method: GenerationMethod,
                             prompt_hash: str,
                             parent_task_id: Optional[str] = None) -> Optional[Task]:
        """Parse LLM response into Task object."""
        try:
            if not response.get("is_valid_task", True):
                return None
            
            name = response.get("name", "")
            task_id = Task.generate_id(language, name)
            
            # Check for duplicates
            if task_id in self.seen_task_names:
                return None
            
            completion = CompletionCriteria(
                precondition=response.get("completion", {}).get("precondition", ""),
                postcondition=response.get("completion", {}).get("postcondition", ""),
                invariants=response.get("completion", {}).get("invariants", ""),
            )
            
            relationships = Relationships(
                composed_of=[Task.generate_id(language, s) for s in response.get("composed_of", [])],
                requires_ability=[Task.generate_id(language, s) for s in response.get("requires_ability", [])],
            )
            
            provenance = Provenance(
                generation_method=generation_method,
                generation_prompt_hash=prompt_hash,
                verification_status=VerificationStatus.UNVERIFIED,
                confidence_score=response.get("confidence", 0.5),
                generation_timestamp=self._get_timestamp(),
                parent_task_id=parent_task_id,
            )
            
            # Filter tags to canonical set
            tags = [t for t in response.get("tags", []) if t in CANONICAL_TAGS]
            
            task = Task(
                id=task_id,
                name=name,
                language=language,
                aliases=response.get("aliases", []),
                concept=response.get("concept"),
                completion=completion,
                relationships=relationships,
                physical=response.get("physical", ""),
                sensing=response.get("sensing", ""),
                cognitive=response.get("cognitive", ""),
                context=response.get("context", ""),
                tags=tags,
                provenance=provenance,
            )
            
            self.seen_task_names.add(task_id)
            return task
            
        except Exception as e:
            return None
    
    # =========================================================================
    # GENERATION METHODS
    # =========================================================================
    
    def generate_from_verb_noun(self, verb: VerbEntry, noun: NounEntry,
                                 persona: Optional[str] = None) -> GenerationResult:
        """Generate a task from a verb-noun combination."""
        task_phrase = f"{verb.verb} {noun.noun}"
        
        # Check if already generated
        potential_id = Task.generate_id(verb.language, task_phrase)
        if potential_id in self.seen_task_names:
            return GenerationResult(task=None, success=False, error="duplicate")
        
        # Build prompt
        persona_prefix = PERSONA_PROMPTS.get(persona, "") if persona else ""
        cultural_context = "General, no specific cultural context" if not noun.cultural_context else noun.cultural_context
        
        prompt = TASK_GENERATION_PROMPT.format(
            task_phrase=task_phrase,
            language=verb.language,
            cultural_context=cultural_context,
            valid_tags=", ".join(sorted(CANONICAL_TAGS)),
        )
        
        if persona_prefix:
            prompt = persona_prefix + "\n\n" + prompt
        
        prompt_hash = self._hash_prompt(prompt)
        
        # Call LLM
        response = self._call_llm(prompt)
        
        if response is None:
            return GenerationResult(
                task=None, 
                success=False, 
                error="LLM call failed",
                prompt_hash=prompt_hash
            )
        
        # Parse response
        task = self._parse_task_response(
            response, 
            verb.language,
            GenerationMethod.VERB_NOUN_MATRIX,
            prompt_hash
        )
        
        if task:
            self.generated_count += 1
            return GenerationResult(task=task, success=True, prompt_hash=prompt_hash)
        else:
            self.failed_count += 1
            return GenerationResult(
                task=None, 
                success=False, 
                error="Invalid task or filtered",
                raw_response=json.dumps(response),
                prompt_hash=prompt_hash
            )
    
    def decompose_task(self, task: Task) -> list[GenerationResult]:
        """Decompose a task into subtasks."""
        prompt = TASK_DECOMPOSITION_PROMPT.format(
            task_name=task.name,
            precondition=task.completion.precondition,
            postcondition=task.completion.postcondition,
            invariants=task.completion.invariants,
            physical=task.physical,
            min_subtasks=self.config.min_subtasks_per_decomposition,
            max_subtasks=self.config.max_subtasks_per_decomposition,
        )
        
        prompt_hash = self._hash_prompt(prompt)
        response = self._call_llm(prompt)
        
        results = []
        
        if response is None:
            return results
        
        for subtask_data in response:
            subtask = self._parse_task_response(
                {
                    "name": subtask_data.get("name"),
                    "completion": subtask_data.get("completion"),
                    "physical": subtask_data.get("physical", ""),
                    "sensing": subtask_data.get("sensing", ""),
                    "cognitive": subtask_data.get("cognitive", ""),
                    "tags": subtask_data.get("tags", []),
                    "is_valid_task": True,
                    "confidence": 0.8,
                },
                task.language,
                GenerationMethod.LLM_DECOMPOSITION,
                prompt_hash,
                parent_task_id=task.id
            )
            
            if subtask:
                # Add relationship back to parent
                subtask.relationships.part_of.append(task.id)
                results.append(GenerationResult(task=subtask, success=True))
        
        return results
    
    def expand_similar_tasks(self, task: Task) -> list[GenerationResult]:
        """Find similar tasks to expand coverage."""
        prompt = TASK_EXPANSION_PROMPT.format(
            task_name=task.name,
            task_description=f"{task.physical}\n{task.context}",
            tags=", ".join(task.tags),
            num_similar=self.config.similar_tasks_per_task,
        )
        
        prompt_hash = self._hash_prompt(prompt)
        response = self._call_llm(prompt)
        
        results = []
        
        if response is None:
            return results
        
        for similar_data in response:
            similar_name = similar_data.get("name", "")
            
            # Generate full task for the similar task
            result = self.generate_from_verb_noun(
                VerbEntry(similar_name.split()[0] if " " in similar_name else similar_name,
                         task.language, "expansion", "transitive", [], "medium"),
                NounEntry(" ".join(similar_name.split()[1:]) if " " in similar_name else "",
                         task.language, "expansion"),
            )
            
            if result.success and result.task:
                result.task.relationships.similar.append(task.id)
                result.task.provenance.generation_method = GenerationMethod.LLM_EXPANSION
                results.append(result)
        
        return results
    
    def evolve_task(self, task: Task, mutation_type: str) -> GenerationResult:
        """Apply Evol-Instruct style mutation to create task variant."""
        prompt = TASK_EVOLUTION_PROMPT.format(
            task_name=task.name,
            precondition=task.completion.precondition,
            postcondition=task.completion.postcondition,
            mutation_type=mutation_type,
        )
        
        prompt_hash = self._hash_prompt(prompt)
        response = self._call_llm(prompt)
        
        if response is None:
            return GenerationResult(task=None, success=False, error="LLM call failed")
        
        evolved_task = self._parse_task_response(
            {
                "name": response.get("name"),
                "completion": response.get("completion"),
                "physical": response.get("physical", ""),
                "sensing": response.get("sensing", ""),
                "cognitive": response.get("cognitive", ""),
                "tags": response.get("tags", []),
                "is_valid_task": True,
                "confidence": 0.75,
            },
            task.language,
            GenerationMethod.EVOLVED,
            prompt_hash,
            parent_task_id=task.id
        )
        
        if evolved_task:
            evolved_task.relationships.similar.append(task.id)
            return GenerationResult(task=evolved_task, success=True)
        
        return GenerationResult(task=None, success=False, error="Evolution failed")
    
    def adapt_culturally(self, task: Task, target_language: str, 
                         target_culture: str) -> GenerationResult:
        """Create culturally adapted version of a task."""
        prompt = CULTURAL_ADAPTATION_PROMPT.format(
            original_task=task.name,
            precondition=task.completion.precondition,
            postcondition=task.completion.postcondition,
            target_language=target_language,
            target_culture=target_culture,
        )
        
        prompt_hash = self._hash_prompt(prompt)
        response = self._call_llm(prompt)
        
        if response is None:
            return GenerationResult(task=None, success=False, error="LLM call failed")
        
        if not response.get("is_culturally_relevant", True):
            return GenerationResult(
                task=None, 
                success=False, 
                error="Not culturally relevant"
            )
        
        adapted_task = self._parse_task_response(
            {
                "name": response.get("name"),
                "completion": response.get("completion"),
                "physical": response.get("physical", ""),
                "sensing": response.get("sensing", ""),
                "cognitive": response.get("cognitive", ""),
                "context": response.get("context", ""),
                "tags": response.get("tags", []),
                "is_valid_task": True,
                "confidence": 0.7,
            },
            target_language,
            GenerationMethod.CULTURAL_ADAPTATION,
            prompt_hash,
            parent_task_id=task.id
        )
        
        if adapted_task:
            adapted_task.concept = task.concept
            adapted_task.related_cultural_variants.append(task.id)
            return GenerationResult(task=adapted_task, success=True)
        
        return GenerationResult(task=None, success=False, error="Adaptation failed")
    
    def validate_task(self, task: Task) -> dict:
        """Validate a task using LLM-as-judge."""
        prompt = VALIDITY_CHECK_PROMPT.format(
            task_name=task.name,
            precondition=task.completion.precondition,
            postcondition=task.completion.postcondition,
            invariants=task.completion.invariants,
        )
        
        response = self._call_llm(prompt, temperature=0.3)  # Lower temp for consistency
        
        if response:
            task.quality_scores = response.get("scores", {})
            overall = response.get("overall_score", 0.5)
            
            if overall >= 0.7:
                task.provenance.verification_status = VerificationStatus.LLM_VALIDATED
            elif overall < 0.4:
                task.provenance.verification_status = VerificationStatus.REJECTED
            
            task.provenance.confidence_score = overall
            return response
        
        return {}
    
    # =========================================================================
    # BATCH GENERATION
    # =========================================================================
    
    def generate_verb_noun_matrix(self, 
                                   language: str = "en",
                                   max_tasks: Optional[int] = None,
                                   use_personas: bool = True) -> Generator[GenerationResult, None, None]:
        """
        Generate tasks from the full verb-noun matrix.
        
        Implements systematic coverage with persona diversity.
        """
        verbs = get_seed_verbs(language)
        nouns = get_seed_nouns(language)
        personas = list(PERSONA_PROMPTS.keys()) if use_personas else [None]
        
        generated = 0
        
        # Create shuffled combinations for better diversity
        combinations = []
        for verb in verbs:
            for noun in nouns:
                # Use verb's typical objects to weight relevance
                relevance = 1.0
                if noun.noun in verb.typical_objects:
                    relevance = 2.0  # Prioritize typical combinations
                if noun.category in ["abstract"] and verb.category == "manipulation":
                    relevance = 0.3  # Deprioritize unlikely combinations
                
                combinations.append((verb, noun, relevance))
        
        # Sort by relevance, then shuffle within relevance tiers
        combinations.sort(key=lambda x: -x[2])
        
        for verb, noun, _ in combinations:
            if max_tasks and generated >= max_tasks:
                break
            
            # Rotate through personas for diversity
            persona = random.choice(personas) if use_personas else None
            
            result = self.generate_from_verb_noun(verb, noun, persona)
            
            if result.success:
                generated += 1
                yield result
                
                # Apply evolution with some probability
                if self.config.enable_evolution and random.random() < self.config.evolution_probability:
                    mutation = random.choice(self.config.evolution_mutations)
                    evolved_result = self.evolve_task(result.task, mutation)
                    if evolved_result.success:
                        generated += 1
                        yield evolved_result
    
    def generate_with_self_consistency(self, verb: VerbEntry, noun: NounEntry,
                                        num_samples: int = 3) -> GenerationResult:
        """
        Generate task with self-consistency validation.
        
        Generate multiple times, keep only if consistent.
        """
        samples = []
        
        for _ in range(num_samples):
            # Vary temperature for diversity
            temp = random.uniform(*self.llm_config.temperature_range)
            result = self.generate_from_verb_noun(verb, noun)
            if result.success:
                samples.append(result.task)
        
        if len(samples) < 2:
            return GenerationResult(task=None, success=False, error="Insufficient samples")
        
        # Check consistency of key fields
        # Simplified: check if postconditions are semantically similar
        postconditions = [t.completion.postcondition for t in samples]
        
        # In production, you'd use embedding similarity here
        # For now, use simple heuristic: all must have similar length/structure
        lengths = [len(p) for p in postconditions]
        if max(lengths) > 2 * min(lengths):
            return GenerationResult(
                task=None, 
                success=False, 
                error="Inconsistent postconditions"
            )
        
        # Return the most detailed version
        best_task = max(samples, key=lambda t: len(t.completion.postcondition))
        best_task.quality_scores["self_consistency"] = len(samples) / num_samples
        
        return GenerationResult(task=best_task, success=True)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_generator(config: GenerationConfig = None, 
                     llm_config: LLMConfig = None) -> TaskGenerator:
    """Create a TaskGenerator with default or custom config."""
    from config import DEFAULT_CONFIG
    
    if config is None:
        config = DEFAULT_CONFIG.generation
    if llm_config is None:
        llm_config = DEFAULT_CONFIG.llm
    
    return TaskGenerator(config, llm_config)


def quick_generate(task_phrase: str, language: str = "en") -> Optional[Task]:
    """Quick generation of a single task for testing."""
    words = task_phrase.lower().split()
    if len(words) < 2:
        return None
    
    verb = VerbEntry(words[0], language, "quick", "transitive", [], "medium")
    noun = NounEntry(" ".join(words[1:]), language, "quick")
    
    generator = create_generator()
    result = generator.generate_from_verb_noun(verb, noun)
    
    return result.task if result.success else None
