"""
Inference module for training plan generation.
"""

import torch
from typing import Dict, List
from model import PoleTrainingPlanGenerator, TrainingPlanPreprocessor
from config import MLConfig


class TrainingPlanInference:
    """Inference engine for generating training plans."""
    
    def __init__(self, model_path: str = None):
        """Initialize inference engine."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = PoleTrainingPlanGenerator(MLConfig).to(self.device)
        self.preprocessor = TrainingPlanPreprocessor()
        self.config = MLConfig
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.model.eval()
    
    def generate_plan(self, user_profile: Dict) -> Dict:
        """
        Generate a training plan for the user.
        
        Args:
            user_profile: User profile dictionary
            
        Returns:
            Generated training plan
        """
        # Preprocess user profile
        profile_text, metadata = self.preprocessor.prepare_user_profile(user_profile)
        
        # Tokenize
        inputs = self.model.tokenizer(
            profile_text,
            max_length=self.config.MAX_SEQ_LENGTH,
            truncation=True,
            return_tensors="pt"
        )
        
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        
        # Generate
        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
        
        # Post-process
        plan = self._post_process_output(logits, metadata)
        return plan
    
    def _post_process_output(self, logits: torch.Tensor, metadata: Dict) -> Dict:
        """Post-process model output into training plan format."""
        # TODO: Implement post-processing logic
        return {
            "status": "success",
            "message": "Training plan generated",
            "metadata": metadata
        }


if __name__ == "__main__":
    # Example usage
    inference = TrainingPlanInference()
    
    user_profile = {
        "age": 28,
        "experience_level": "intermediate",
        "fitness_level": 7,
        "available_days_per_week": 4,
        "goals": ["improve upper body strength", "learn advanced moves"]
    }
    
    # plan = inference.generate_plan(user_profile)
    # print(plan)
