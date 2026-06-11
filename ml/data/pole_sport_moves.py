"""
Pole sport specific moves and progression data.
"""

POLE_SPORT_MOVES = {
    "basic_grip": {
        "id": "basic_grip",
        "name": "Basic Grip",
        "level": "basic",
        "description": "Fundamental grip technique for all pole moves",
        "prerequisites": [],
        "progression_steps": [
            "Warm-up grip",
            "Extended hold",
            "Single handed holds",
            "Combination with body contact"
        ],
        "primary_muscles": ["forearm", "hand", "grip"],
        "secondary_muscles": ["wrist"],
        "conditioning_exercises": [
            "pole_basic_grip",
            "squeeze_ball_grip",
            "resistance_band_grip"
        ],
        "safety_tips": [
            "Keep fingers spread for better grip",
            "Maintain contact with palm",
            "Avoid over-gripping which causes fatigue"
        ]
    },
    "pole_sit": {
        "id": "pole_sit",
        "name": "Pole Sit",
        "level": "basic",
        "description": "Basic sitting position on the pole",
        "prerequisites": ["basic_grip"],
        "progression_steps": [
            "Sitting position learning",
            "Hold duration increase",
            "Transition practice",
            "Crossed leg variations"
        ],
        "primary_muscles": ["leg", "grip", "core"],
        "secondary_muscles": ["arm", "shoulder"],
        "conditioning_exercises": [
            "pole_pole_sit_progression",
            "leg_strength_training",
            "core_engagement"
        ],
        "safety_tips": [
            "Ensure proper grip before sitting",
            "Keep core engaged",
            "Practice dismount safely"
        ]
    },
    "spin": {
        "id": "spin",
        "name": "Basic Spin",
        "level": "intermediate",
        "description": "Learn to use momentum on a spinning pole",
        "prerequisites": ["basic_grip", "pole_sit"],
        "progression_steps": [
            "Understand momentum",
            "Gentle spin practice",
            "Increased rotation speed",
            "Control and dismount"
        ],
        "primary_muscles": ["core", "leg", "grip"],
        "secondary_muscles": ["shoulder", "arm"],
        "conditioning_exercises": [
            "pole_spin_conditioning",
            "core_rotation_exercises",
            "balance_training"
        ],
        "safety_tips": [
            "Start with low speed",
            "Ensure proper grip pressure",
            "Have spotter present initially",
            "Know safe dismount technique"
        ]
    },
    "invert": {
        "id": "invert",
        "name": "Invert",
        "level": "advanced",
        "description": "Flip upside down on the pole",
        "prerequisites": ["pole_sit", "spin"],
        "progression_steps": [
            "Shoulder shrug practice",
            "Partial inversions",
            "Full inversion with support",
            "Controlled inversions",
            "Hold variations"
        ],
        "primary_muscles": ["core", "shoulder", "arm"],
        "secondary_muscles": ["back", "leg"],
        "conditioning_exercises": [
            "pole_invert_strength",
            "shoulder_shrug_progression",
            "core_strength_building",
            "inversions_preparation"
        ],
        "safety_tips": [
            "ESSENTIAL: Use crash mat",
            "Practice with qualified instructor",
            "Build shoulder strength first",
            "Master grip strength techniques",
            "Know proper head positioning"
        ],
        "common_mistakes": [
            "Rushing progression",
            "Insufficient core strength",
            "Improper grip technique",
            "Not wearing protective gear"
        ]
    },
    "shoulder_mount": {
        "id": "shoulder_mount",
        "name": "Shoulder Mount",
        "level": "advanced",
        "description": "Position pole across shoulders for advanced moves",
        "prerequisites": ["invert", "pole_sit"],
        "progression_steps": [
            "Shoulder placement practice",
            "Hold without movement",
            "Small movements",
            "Combination with other moves"
        ],
        "primary_muscles": ["shoulder", "core", "arm"],
        "secondary_muscles": ["back", "neck"],
        "conditioning_exercises": [
            "shoulder_flexibility_routine",
            "neck_strengthening",
            "shoulder_stabilization"
        ],
        "safety_tips": [
            "Protect neck area",
            "Ensure proper padding/grip",
            "Gradual progression essential",
            "Stop if experiencing pain"
        ]
    }
}


def get_move_progression_path(start_level: str = "basic") -> list:
    """
    Get recommended progression path for pole sport moves.
    
    Args:
        start_level: Starting difficulty level
        
    Returns:
        List of recommended moves in progression order
    """
    level_order = ["basic", "intermediate", "advanced", "elite"]
    
    if start_level not in level_order:
        start_level = "basic"
    
    start_idx = level_order.index(start_level)
    progression_levels = level_order[start_idx:]
    
    moves_by_level = {}
    for level in progression_levels:
        moves_by_level[level] = [
            move for move in POLE_SPORT_MOVES.values()
            if move["level"] == level
        ]
    
    progression = []
    for level in progression_levels:
        progression.extend(moves_by_level.get(level, []))
    
    return progression


def get_prerequisites_for_move(move_id: str) -> list:
    """
    Get all prerequisites for a specific move.
    
    Args:
        move_id: ID of the pole sport move
        
    Returns:
        List of prerequisite move IDs
    """
    move = POLE_SPORT_MOVES.get(move_id)
    if not move:
        return []
    
    prerequisites = move.get("prerequisites", [])
    
    # Recursively get prerequisites of prerequisites
    all_prerequisites = set()
    to_process = list(prerequisites)
    
    while to_process:
        prereq_id = to_process.pop(0)
        if prereq_id not in all_prerequisites:
            all_prerequisites.add(prereq_id)
            prereq_move = POLE_SPORT_MOVES.get(prereq_id)
            if prereq_move:
                to_process.extend(prereq_move.get("prerequisites", []))
    
    return list(all_prerequisites)


if __name__ == "__main__":
    print("Pole Sport Moves data loaded")
    print(f"Total moves defined: {len(POLE_SPORT_MOVES)}")
    
    # Example
    invert_prerequisites = get_prerequisites_for_move("invert")
    print(f"\nPrerequisites for 'invert': {invert_prerequisites}")
    
    progression = get_move_progression_path("basic")
    print(f"\nProgression path from basic:")
    for move in progression:
        print(f"  - {move['name']} ({move['level']})")
