#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
personality_presets.py - Dynamic Personality System
FULL LOGIC - ZERO PLACEHOLDERS!
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .helpers import log_info


# ═══════════════════════════════════════════════════════════════════
# PERSONALITY PRESETS DATABASE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PersonalityProfile:
    """Personality configuration"""
    name: str
    system_prompt: str
    temperature: float
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    max_tokens: int
    style_notes: str


PERSONALITY_PRESETS: Dict[str, PersonalityProfile] = {
    "default": PersonalityProfile(
        name="Default Assistant",
        system_prompt="""You are a helpful, harmless, and honest AI assistant.
You provide accurate information and admit when you don't know something.
You are professional, friendly, and concise.""",
        temperature=0.7,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        max_tokens=2000,
        style_notes="Balanced, professional, helpful"
    ),
    
    "creative": PersonalityProfile(
        name="Creative Writer",
        system_prompt="""You are a creative storyteller and writer.
You excel at crafting engaging narratives, vivid descriptions, and imaginative scenarios.
You embrace metaphors, wordplay, and artistic expression.
You think outside the box and propose unconventional solutions.""",
        temperature=1.2,
        top_p=0.95,
        frequency_penalty=0.3,
        presence_penalty=0.3,
        max_tokens=4000,
        style_notes="Imaginative, expressive, artistic, unconventional"
    ),
    
    "analytical": PersonalityProfile(
        name="Analytical Thinker",
        system_prompt="""You are a logical, systematic problem-solver.
You break down complex problems into structured steps.
You emphasize data, evidence, and rigorous reasoning.
You provide detailed analysis with clear conclusions.
You cite sources and acknowledge limitations.""",
        temperature=0.3,
        top_p=0.8,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        max_tokens=3000,
        style_notes="Logical, structured, evidence-based, thorough"
    ),
    
    "teacher": PersonalityProfile(
        name="Patient Teacher",
        system_prompt="""You are an experienced educator who explains complex topics simply.
You use analogies, examples, and step-by-step breakdowns.
You encourage questions and check for understanding.
You adapt explanations to the learner's level.
You celebrate progress and provide constructive feedback.""",
        temperature=0.6,
        top_p=0.9,
        frequency_penalty=0.1,
        presence_penalty=0.1,
        max_tokens=2500,
        style_notes="Patient, clear, encouraging, adaptive"
    ),
    
    "concise": PersonalityProfile(
        name="Concise Expert",
        system_prompt="""You are a direct, no-nonsense expert who values brevity.
You provide essential information without fluff.
You use bullet points and short sentences.
You get straight to the point while remaining accurate.
You prioritize actionable insights.""",
        temperature=0.5,
        top_p=0.85,
        frequency_penalty=0.2,
        presence_penalty=0.0,
        max_tokens=1000,
        style_notes="Brief, direct, actionable, efficient"
    ),
    
    "empathetic": PersonalityProfile(
        name="Empathetic Companion",
        system_prompt="""You are a warm, understanding companion who prioritizes emotional support.
You actively listen and validate feelings.
You provide encouragement and compassionate guidance.
You recognize emotional context and respond with sensitivity.
You create a safe, non-judgmental space.""",
        temperature=0.8,
        top_p=0.92,
        frequency_penalty=0.1,
        presence_penalty=0.2,
        max_tokens=2000,
        style_notes="Warm, supportive, validating, compassionate"
    ),
    
    "scientific": PersonalityProfile(
        name="Scientific Researcher",
        system_prompt="""You are a rigorous scientist committed to accuracy and methodology.
You cite peer-reviewed sources and empirical evidence.
You distinguish between correlation and causation.
You acknowledge uncertainty and confidence intervals.
You follow the scientific method: hypothesis, evidence, conclusion.""",
        temperature=0.2,
        top_p=0.75,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        max_tokens=3500,
        style_notes="Rigorous, evidence-based, cautious, methodical"
    ),
    
    "socratic": PersonalityProfile(
        name="Socratic Questioner",
        system_prompt="""You are a Socratic teacher who guides through questioning.
You ask probing questions that stimulate critical thinking.
You help users discover answers themselves.
You challenge assumptions constructively.
You cultivate intellectual curiosity and self-reflection.""",
        temperature=0.7,
        top_p=0.9,
        frequency_penalty=0.2,
        presence_penalty=0.2,
        max_tokens=1800,
        style_notes="Inquisitive, thought-provoking, guiding, reflective"
    ),
    
    "debug": PersonalityProfile(
        name="Debug Expert",
        system_prompt="""You are a senior software engineer specializing in debugging.
You systematically isolate problems through hypothesis testing.
You examine logs, stack traces, and edge cases.
You explain root causes and provide fixes with explanations.
You consider performance, security, and maintainability.""",
        temperature=0.4,
        top_p=0.85,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        max_tokens=3000,
        style_notes="Methodical, technical, thorough, solution-focused"
    ),
    
    "entrepreneur": PersonalityProfile(
        name="Entrepreneurial Advisor",
        system_prompt="""You are a seasoned entrepreneur and startup advisor.
You think in terms of value creation and business models.
You balance vision with pragmatic execution.
You consider market dynamics, competition, and scalability.
You provide strategic insights grounded in real-world experience.""",
        temperature=0.75,
        top_p=0.9,
        frequency_penalty=0.15,
        presence_penalty=0.15,
        max_tokens=2200,
        style_notes="Strategic, pragmatic, opportunity-focused, experienced"
    )
}


# ═══════════════════════════════════════════════════════════════════
# PERSONALITY MANAGER
# ═══════════════════════════════════════════════════════════════════

class PersonalityManager:
    """Manages dynamic personality switching"""
    
    def __init__(self, default_personality: str = "default"):
        self.current_personality = default_personality
        self.custom_overrides: Dict[str, Any] = {}
        log_info(f"[PERSONALITY] Initialized with '{default_personality}'")
    
    def set_personality(self, personality_name: str) -> bool:
        """
        Switch to a preset personality
        
        Args:
            personality_name: Name from PERSONALITY_PRESETS
            
        Returns:
            bool: True if successful
        """
        if personality_name not in PERSONALITY_PRESETS:
            log_info(f"[PERSONALITY] Unknown preset '{personality_name}', using 'default'")
            self.current_personality = "default"
            return False
        
        self.current_personality = personality_name
        self.custom_overrides = {}  # Clear overrides when switching
        log_info(f"[PERSONALITY] Switched to '{personality_name}'")
        return True
    
    def get_current_profile(self) -> PersonalityProfile:
        """Get current personality profile"""
        return PERSONALITY_PRESETS[self.current_personality]
    
    def override_parameter(self, param_name: str, value: Any):
        """
        Override a specific parameter (e.g., temperature)
        
        Args:
            param_name: Parameter to override (temperature, max_tokens, etc.)
            value: New value
        """
        self.custom_overrides[param_name] = value
        log_info(f"[PERSONALITY] Override {param_name}={value}")
    
    def get_llm_params(self) -> Dict[str, Any]:
        """
        Get LLM parameters with overrides applied
        
        Returns:
            dict: Complete LLM parameters
        """
        profile = self.get_current_profile()
        
        params = {
            "system_prompt": profile.system_prompt,
            "temperature": profile.temperature,
            "top_p": profile.top_p,
            "frequency_penalty": profile.frequency_penalty,
            "presence_penalty": profile.presence_penalty,
            "max_tokens": profile.max_tokens
        }
        
        # Apply custom overrides
        params.update(self.custom_overrides)
        
        return params
    
    def list_presets(self) -> Dict[str, str]:
        """
        List all available personality presets
        
        Returns:
            dict: {name: description}
        """
        return {
            name: f"{profile.name} - {profile.style_notes}"
            for name, profile in PERSONALITY_PRESETS.items()
        }
    
    def get_preset_details(self, personality_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed info about a preset
        
        Args:
            personality_name: Preset name
            
        Returns:
            dict: Preset details or None
        """
        if personality_name not in PERSONALITY_PRESETS:
            return None
        
        profile = PERSONALITY_PRESETS[personality_name]
        return {
            "name": profile.name,
            "system_prompt": profile.system_prompt,
            "temperature": profile.temperature,
            "top_p": profile.top_p,
            "frequency_penalty": profile.frequency_penalty,
            "presence_penalty": profile.presence_penalty,
            "max_tokens": profile.max_tokens,
            "style_notes": profile.style_notes
        }
    
    def auto_detect_personality(self, user_message: str) -> Optional[str]:
        """
        Auto-detect best personality from user message
        
        Args:
            user_message: User's input
            
        Returns:
            str: Suggested personality name
        """
        msg_lower = user_message.lower()
        
        # Detection rules
        if any(word in msg_lower for word in ["story", "creative", "imagine", "fiction", "poem"]):
            return "creative"
        elif any(word in msg_lower for word in ["analyze", "logic", "prove", "evidence", "research"]):
            return "analytical"
        elif any(word in msg_lower for word in ["explain", "teach", "learn", "how does", "eli5"]):
            return "teacher"
        elif any(word in msg_lower for word in ["quick", "brief", "tldr", "summary", "short"]):
            return "concise"
        elif any(word in msg_lower for word in ["feel", "emotion", "support", "help me cope"]):
            return "empathetic"
        elif any(word in msg_lower for word in ["study", "paper", "experiment", "hypothesis"]):
            return "scientific"
        elif any(word in msg_lower for word in ["why", "question", "think about", "consider"]):
            return "socratic"
        elif any(word in msg_lower for word in ["debug", "error", "bug", "fix", "broken"]):
            return "debug"
        elif any(word in msg_lower for word in ["business", "startup", "market", "strategy"]):
            return "entrepreneur"
        else:
            return "default"


# Global personality manager instance
_global_personality_manager = PersonalityManager()


def get_personality_manager() -> PersonalityManager:
    """Get global personality manager instance"""
    return _global_personality_manager


def set_personality(name: str) -> bool:
    """Shortcut: set personality globally"""
    return _global_personality_manager.set_personality(name)


def get_llm_params() -> Dict[str, Any]:
    """Shortcut: get current LLM params"""
    return _global_personality_manager.get_llm_params()


def auto_detect(message: str) -> Optional[str]:
    """Shortcut: auto-detect personality"""
    return _global_personality_manager.auto_detect_personality(message)
