"""
Model definitions for training plan generation.
"""

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from typing import Dict, Tuple


class PoleTrainingPlanGenerator(nn.Module):
    """
    Neural network model for generating personalized pole sport training plans.
    
    This model takes user profile information and generates a sequence of 
    training exercises tailored to their experience level, fitness, and goals.
    """
    
    def __init__(self, config):
        """Initialize the model."""
        super().__init__()
        self.config = config
        
        # Load pre-trained transformer
        self.encoder = AutoModel.from_pretrained(config.TRANSFORMER_BASE)
        self.tokenizer = AutoTokenizer.from_pretrained(config.TRANSFORMER_BASE)
        
        # Training plan generation layers
        self.decoder = nn.Sequential(
            nn.Linear(self.encoder.config.hidden_size, config.HIDDEN_SIZE),
            nn.ReLU(),
            nn.Dropout(config.DROPOUT_RATE),
            nn.Linear(config.HIDDEN_SIZE, config.HIDDEN_SIZE),
            nn.ReLU(),
            nn.Dropout(config.DROPOUT_RATE),
            nn.Linear(config.HIDDEN_SIZE, config.VOCAB_SIZE)
        )
        
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the model.
        
        Args:
            input_ids: Token IDs from user profile
            attention_mask: Attention mask for padding tokens
            
        Returns:
            Logits for training plan generation
        """
        encoder_output = self.encoder(
            input_ids=input_ids, 
            attention_mask=attention_mask
        )
        
        # Use [CLS] token representation
        cls_representation = encoder_output.last_hidden_state[:, 0, :]
        
        # Generate training plan
        logits = self.decoder(cls_representation)
        return logits


class TrainingPlanPreprocessor:
    """Preprocess user profile data for model input."""
    
    @staticmethod
    def prepare_user_profile(user_profile: Dict) -> Tuple[str, Dict]:
        """
        Convert user profile dict to model-ready format.
        
        Args:
            user_profile: User information dict
            
        Returns:
            Formatted input string and metadata
        """
        template = (
            f"Age: {user_profile['age']}, "
            f"Experience: {user_profile['experience_level']}, "
            f"Fitness: {user_profile['fitness_level']}/10, "
            f"Days/week: {user_profile['available_days_per_week']}, "
            f"Goals: {', '.join(user_profile['goals'])}"
        )
        
        metadata = {
            "age": user_profile.get("age"),
            "experience_level": user_profile.get("experience_level"),
            "fitness_level": user_profile.get("fitness_level"),
        }
        
        return template, metadata


if __name__ == "__main__":
    from config import MLConfig
    
    # Test model initialization
    model = PoleTrainingPlanGenerator(MLConfig)
    print(f"Model initialized with {sum(p.numel() for p in model.parameters())} parameters")
