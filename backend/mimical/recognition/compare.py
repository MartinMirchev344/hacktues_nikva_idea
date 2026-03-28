from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .mediapipe_utils import DEFAULT_TARGET_FRAME_COUNT, extract_landmark_sequence_from_video, normalize_sign_name

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates_landmarks"
SHAPE_SCORE_WEIGHT = 0.5
POSITION_SCORE_WEIGHT = 0.3
MOTION_SCORE_WEIGHT = 0.2


CANONICAL_HAND_SHAPES = {
    "open": np.array(
        [
            [0.00, 0.00, 0.00],
            [0.04, -0.03, 0.00],
            [0.08, -0.06, 0.00],
            [0.12, -0.09, 0.00],
            [0.16, -0.11, 0.00],
            [0.03, -0.10, 0.00],
            [0.03, -0.20, 0.00],
            [0.03, -0.31, 0.00],
            [0.03, -0.43, 0.00],
            [0.00, -0.10, 0.00],
            [0.00, -0.22, 0.00],
            [0.00, -0.35, 0.00],
            [0.00, -0.48, 0.00],
            [-0.03, -0.09, 0.00],
            [-0.03, -0.20, 0.00],
            [-0.03, -0.31, 0.00],
            [-0.03, -0.43, 0.00],
            [-0.06, -0.07, 0.00],
            [-0.06, -0.16, 0.00],
            [-0.06, -0.26, 0.00],
            [-0.06, -0.36, 0.00],
        ],
        dtype=np.float32,
    ),
    "fist": np.array(
        [
            [0.00, 0.00, 0.00],
            [0.04, -0.01, 0.00],
            [0.07, -0.03, 0.00],
            [0.09, -0.05, 0.00],
            [0.12, -0.05, 0.00],
            [0.03, -0.08, 0.00],
            [0.03, -0.12, 0.00],
            [0.03, -0.14, 0.00],
            [0.03, -0.14, 0.00],
            [0.00, -0.08, 0.00],
            [0.00, -0.12, 0.00],
            [0.00, -0.14, 0.00],
            [0.00, -0.14, 0.00],
            [-0.03, -0.08, 0.00],
            [-0.03, -0.11, 0.00],
            [-0.03, -0.13, 0.00],
            [-0.03, -0.13, 0.00],
            [-0.06, -0.07, 0.00],
            [-0.06, -0.10, 0.00],
            [-0.06, -0.12, 0.00],
            [-0.06, -0.12, 0.00],
        ],
        dtype=np.float32,
    ),
    "open_spread": np.array(
        [
            [0.00, 0.00, 0.00],
            [0.07, -0.03, 0.00],
            [0.12, -0.07, 0.00],
            [0.17, -0.12, 0.00],
            [0.22, -0.16, 0.00],
            [0.08, -0.10, 0.00],
            [0.10, -0.22, 0.00],
            [0.12, -0.35, 0.00],
            [0.15, -0.50, 0.00],
            [0.02, -0.11, 0.00],
            [0.02, -0.24, 0.00],
            [0.02, -0.38, 0.00],
            [0.02, -0.53, 0.00],
            [-0.06, -0.10, 0.00],
            [-0.08, -0.22, 0.00],
            [-0.10, -0.35, 0.00],
            [-0.12, -0.49, 0.00],
            [-0.14, -0.08, 0.00],
            [-0.17, -0.19, 0.00],
            [-0.20, -0.29, 0.00],
            [-0.24, -0.39, 0.00],
        ],
        dtype=np.float32,
    ),
    "goodbye_closed": np.array(
        [
            [0.00, 0.00, 0.00],
            [0.06, -0.02, 0.00],
            [0.10, -0.05, 0.00],
            [0.14, -0.08, 0.00],
            [0.18, -0.10, 0.00],
            [0.08, -0.08, 0.00],
            [0.10, -0.14, 0.00],
            [0.11, -0.18, 0.00],
            [0.12, -0.19, 0.00],
            [0.02, -0.09, 0.00],
            [0.02, -0.15, 0.00],
            [0.02, -0.19, 0.00],
            [0.02, -0.20, 0.00],
            [-0.06, -0.09, 0.00],
            [-0.07, -0.14, 0.00],
            [-0.08, -0.18, 0.00],
            [-0.09, -0.19, 0.00],
            [-0.13, -0.08, 0.00],
            [-0.15, -0.12, 0.00],
            [-0.16, -0.16, 0.00],
            [-0.17, -0.17, 0.00],
        ],
        dtype=np.float32,
    ),
    "index_point": np.array(
        [
            [0.00, 0.00, 0.00],
            [0.04, -0.01, 0.00],
            [0.06, -0.03, 0.00],
            [0.08, -0.05, 0.00],
            [0.11, -0.06, 0.00],
            [0.03, -0.10, 0.00],
            [0.03, -0.22, 0.00],
            [0.03, -0.36, 0.00],
            [0.03, -0.52, 0.00],
            [0.00, -0.08, 0.00],
            [0.00, -0.12, 0.00],
            [0.00, -0.15, 0.00],
            [0.00, -0.16, 0.00],
            [-0.03, -0.08, 0.00],
            [-0.03, -0.11, 0.00],
            [-0.03, -0.13, 0.00],
            [-0.03, -0.14, 0.00],
            [-0.06, -0.07, 0.00],
            [-0.06, -0.10, 0.00],
            [-0.06, -0.12, 0.00],
            [-0.06, -0.13, 0.00],
        ],
        dtype=np.float32,
    ),
    "two_finger_thumb_open": np.array(
        [
            [0.00, 0.00, 0.00],
            [0.05, -0.02, 0.00],
            [0.10, -0.03, 0.00],
            [0.15, -0.03, 0.00],
            [0.20, -0.03, 0.00],
            [0.02, -0.10, 0.00],
            [0.00, -0.22, 0.00],
            [-0.03, -0.36, 0.00],
            [-0.07, -0.50, 0.00],
            [-0.02, -0.10, 0.00],
            [0.03, -0.23, 0.00],
            [0.08, -0.36, 0.00],
            [0.13, -0.49, 0.00],
            [-0.03, -0.08, 0.00],
            [-0.03, -0.12, 0.00],
            [-0.03, -0.14, 0.00],
            [-0.03, -0.15, 0.00],
            [-0.06, -0.07, 0.00],
            [-0.06, -0.10, 0.00],
            [-0.06, -0.12, 0.00],
            [-0.06, -0.13, 0.00],
        ],
        dtype=np.float32,
    ),
    "two_finger_thumb_closed": np.array(
        [
            [0.00, 0.00, 0.00],
            [0.05, -0.02, 0.00],
            [0.09, -0.04, 0.00],
            [0.12, -0.05, 0.00],
            [0.15, -0.05, 0.00],
            [0.02, -0.09, 0.00],
            [0.01, -0.14, 0.00],
            [0.01, -0.18, 0.00],
            [0.00, -0.19, 0.00],
            [-0.01, -0.09, 0.00],
            [0.01, -0.14, 0.00],
            [0.03, -0.18, 0.00],
            [0.05, -0.19, 0.00],
            [-0.03, -0.08, 0.00],
            [-0.03, -0.11, 0.00],
            [-0.03, -0.13, 0.00],
            [-0.03, -0.14, 0.00],
            [-0.06, -0.07, 0.00],
            [-0.06, -0.10, 0.00],
            [-0.06, -0.12, 0.00],
            [-0.06, -0.13, 0.00],
        ],
        dtype=np.float32,
    ),
}


def _with_updates(base_name: str, updates: dict[int, tuple[float, float, float]]) -> np.ndarray:
    shape = np.array(CANONICAL_HAND_SHAPES[base_name], copy=True)
    for index, point in updates.items():
        shape[index] = np.array(point, dtype=np.float32)
    return shape


CANONICAL_HAND_SHAPES["b_hand"] = _with_updates(
    "open",
    {
        1: (0.01, -0.02, 0.0),
        2: (0.00, -0.03, 0.0),
        3: (-0.01, -0.03, 0.0),
        4: (-0.02, -0.02, 0.0),
    },
)
CANONICAL_HAND_SHAPES["three_hand"] = _with_updates(
    "open",
    {
        17: (-0.06, -0.07, 0.0),
        18: (-0.06, -0.10, 0.0),
        19: (-0.06, -0.12, 0.0),
        20: (-0.06, -0.13, 0.0),
    },
)
CANONICAL_HAND_SHAPES["g_hand"] = _with_updates(
    "index_point",
    {
        1: (0.05, -0.01, 0.0),
        2: (0.10, 0.00, 0.0),
        3: (0.16, 0.01, 0.0),
        4: (0.23, 0.01, 0.0),
        8: (0.32, -0.02, 0.0),
        6: (0.14, -0.03, 0.0),
        7: (0.24, -0.02, 0.0),
    },
)
CANONICAL_HAND_SHAPES["y_hand"] = _with_updates(
    "open_spread",
    {
        5: (0.04, -0.08, 0.0),
        6: (0.04, -0.12, 0.0),
        7: (0.04, -0.14, 0.0),
        8: (0.04, -0.15, 0.0),
        9: (0.01, -0.08, 0.0),
        10: (0.01, -0.12, 0.0),
        11: (0.01, -0.14, 0.0),
        12: (0.01, -0.15, 0.0),
        13: (-0.02, -0.08, 0.0),
        14: (-0.02, -0.12, 0.0),
        15: (-0.02, -0.14, 0.0),
        16: (-0.02, -0.15, 0.0),
        17: (-0.05, -0.06, 0.0),
        18: (-0.08, -0.18, 0.0),
        19: (-0.12, -0.30, 0.0),
        20: (-0.18, -0.42, 0.0),
    },
)
CANONICAL_HAND_SHAPES["flat_o"] = _with_updates(
    "open",
    {
        4: (0.08, -0.10, 0.0),
        8: (0.04, -0.14, 0.0),
        12: (0.01, -0.15, 0.0),
        16: (-0.02, -0.14, 0.0),
        20: (-0.05, -0.11, 0.0),
        7: (0.04, -0.16, 0.0),
        11: (0.01, -0.17, 0.0),
        15: (-0.02, -0.16, 0.0),
        19: (-0.05, -0.13, 0.0),
    },
)
CANONICAL_HAND_SHAPES["c_hand"] = _with_updates(
    "open",
    {
        4: (0.16, -0.02, 0.0),
        8: (0.10, -0.18, 0.0),
        12: (0.04, -0.28, 0.0),
        16: (-0.02, -0.27, 0.0),
        20: (-0.08, -0.20, 0.0),
        7: (0.09, -0.15, 0.0),
        11: (0.04, -0.23, 0.0),
        15: (-0.01, -0.23, 0.0),
        19: (-0.06, -0.17, 0.0),
    },
)
CANONICAL_HAND_SHAPES["six_hand"] = _with_updates(
    "open",
    {
        4: (-0.04, -0.28, 0.0),
        20: (-0.05, -0.29, 0.0),
    },
)
CANONICAL_HAND_SHAPES["seven_hand"] = _with_updates(
    "open",
    {
        4: (-0.02, -0.35, 0.0),
        16: (-0.02, -0.35, 0.0),
    },
)
CANONICAL_HAND_SHAPES["eight_hand"] = _with_updates(
    "open",
    {
        4: (0.01, -0.36, 0.0),
        12: (0.01, -0.36, 0.0),
    },
)
CANONICAL_HAND_SHAPES["nine_hand"] = _with_updates(
    "open",
    {
        4: (0.04, -0.32, 0.0),
        8: (0.04, -0.32, 0.0),
    },
)
CANONICAL_HAND_SHAPES["thumb_up"] = _with_updates(
    "fist",
    {
        1: (0.03, -0.10, 0.0),
        2: (0.05, -0.21, 0.0),
        3: (0.07, -0.34, 0.0),
        4: (0.08, -0.49, 0.0),
    },
)
CANONICAL_HAND_SHAPES["w_hand"] = _with_updates(
    "open_spread",
    {
        1: (0.02, -0.02, 0.0),
        2: (0.00, -0.03, 0.0),
        3: (-0.01, -0.03, 0.0),
        4: (-0.02, -0.02, 0.0),
        17: (-0.06, -0.08, 0.0),
        18: (-0.06, -0.11, 0.0),
        19: (-0.06, -0.13, 0.0),
        20: (-0.06, -0.14, 0.0),
    },
)
CANONICAL_HAND_SHAPES["l_hand"] = _with_updates(
    "index_point",
    {
        1: (0.06, -0.02, 0.0),
        2: (0.12, -0.01, 0.0),
        3: (0.18, 0.00, 0.0),
        4: (0.25, 0.01, 0.0),
    },
)
CANONICAL_HAND_SHAPES["hook_index"] = _with_updates(
    "index_point",
    {
        6: (0.03, -0.18, 0.0),
        7: (0.06, -0.27, 0.0),
        8: (0.11, -0.31, 0.0),
    },
)
CANONICAL_HAND_SHAPES["claw_hand"] = _with_updates(
    "open_spread",
    {
        7: (0.10, -0.24, 0.0),
        8: (0.08, -0.20, 0.0),
        11: (0.02, -0.26, 0.0),
        12: (0.01, -0.22, 0.0),
        15: (-0.08, -0.24, 0.0),
        16: (-0.06, -0.20, 0.0),
        19: (-0.16, -0.20, 0.0),
        20: (-0.12, -0.15, 0.0),
    },
)

DEFAULT_BODY_ANCHORS = {
    "forehead": np.array([0.50, 0.24, 0.00], dtype=np.float32),
    "mouth": np.array([0.50, 0.35, 0.00], dtype=np.float32),
    "chin": np.array([0.50, 0.42, 0.00], dtype=np.float32),
    "left_shoulder": np.array([0.38, 0.62, 0.00], dtype=np.float32),
    "right_shoulder": np.array([0.62, 0.62, 0.00], dtype=np.float32),
    "shoulder_center": np.array([0.50, 0.62, 0.00], dtype=np.float32),
    "nose": np.array([0.50, 0.31, 0.00], dtype=np.float32),
    "scale_hint": 0.24,
}

TEMPLATE_PROFILES = {
    "hello": {
        "label": "hello",
        "anchor": "forehead",
        "hand_shape": "open",
        "path": "hello_wave",
        "hand_scale": 0.18,
    },
    "thank_you": {
        "label": "thank you",
        "anchor": "chin",
        "hand_shape": "open",
        "path": "thank_you_release",
        "hand_scale": 0.17,
    },
    "yes": {
        "label": "yes",
        "anchor": "shoulder_center",
        "hand_shape": "fist",
        "path": "yes_bob",
        "hand_scale": 0.15,
    },
    "goodbye": {
        "label": "goodbye",
        "anchor": "forehead",
        "hand_shape": "open_spread",
        "path": "goodbye_wave",
        "shape_motion": "goodbye_wave",
        "hand_scale": 0.18,
    },
    "please": {
        "label": "please",
        "anchor": "shoulder_center",
        "hand_shape": "open",
        "path": "chest_circle",
        "hand_scale": 0.17,
    },
    "sorry": {
        "label": "sorry",
        "anchor": "shoulder_center",
        "hand_shape": "fist",
        "path": "small_chest_circle",
        "hand_scale": 0.16,
    },
    "no": {
        "label": "no",
        "anchor": "mouth",
        "hand_shape": "two_finger_thumb_open",
        "path": "no_snap",
        "shape_motion": "no_snap",
        "hand_scale": 0.17,
    },
    "mother": {
        "label": "mother",
        "anchor": "chin",
        "hand_shape": "open_spread",
        "path": "chin_tap",
        "hand_scale": 0.18,
    },
    "father": {
        "label": "father",
        "anchor": "forehead",
        "hand_shape": "open_spread",
        "path": "forehead_tap",
        "hand_scale": 0.18,
    },
    "brother": {
        "label": "brother",
        "anchor": "forehead",
        "hand_shape": "l_hand",
        "path": "brother_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "l_hand",
        "secondary_path": "brother_secondary",
        "secondary_hand_scale": 0.17,
    },
    "sister": {
        "label": "sister",
        "anchor": "chin",
        "hand_shape": "l_hand",
        "path": "sister_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "l_hand",
        "secondary_path": "sister_secondary",
        "secondary_hand_scale": 0.17,
    },
    "friend": {
        "label": "friend",
        "anchor": "shoulder_center",
        "hand_shape": "hook_index",
        "path": "friend_primary",
        "hand_scale": 0.16,
        "secondary_hand_shape": "hook_index",
        "secondary_path": "friend_secondary",
        "secondary_hand_scale": 0.16,
    },
    "red": {
        "label": "red",
        "anchor": "mouth",
        "hand_shape": "index_point",
        "path": "mouth_brush_down",
        "hand_scale": 0.17,
    },
    "black": {
        "label": "black",
        "anchor": "forehead",
        "hand_shape": "index_point",
        "path": "forehead_slide",
        "hand_scale": 0.17,
    },
    "one": {
        "label": "one",
        "anchor": "shoulder_center",
        "hand_shape": "index_point",
        "path": "static_center",
        "hand_scale": 0.17,
    },
    "two": {
        "label": "two",
        "anchor": "shoulder_center",
        "hand_shape": "two_finger_thumb_open",
        "path": "static_center",
        "hand_scale": 0.17,
    },
    "three": {
        "label": "three",
        "anchor": "shoulder_center",
        "hand_shape": "three_hand",
        "path": "static_center",
        "hand_scale": 0.17,
    },
    "four": {
        "label": "four",
        "anchor": "shoulder_center",
        "hand_shape": "b_hand",
        "path": "static_center",
        "hand_scale": 0.18,
    },
    "five": {
        "label": "five",
        "anchor": "shoulder_center",
        "hand_shape": "open_spread",
        "path": "static_center",
        "hand_scale": 0.18,
    },
    "six": {
        "label": "six",
        "anchor": "shoulder_center",
        "hand_shape": "six_hand",
        "path": "static_center",
        "hand_scale": 0.18,
    },
    "seven": {
        "label": "seven",
        "anchor": "shoulder_center",
        "hand_shape": "seven_hand",
        "path": "static_center",
        "hand_scale": 0.18,
    },
    "eight": {
        "label": "eight",
        "anchor": "shoulder_center",
        "hand_shape": "eight_hand",
        "path": "static_center",
        "hand_scale": 0.18,
    },
    "nine": {
        "label": "nine",
        "anchor": "shoulder_center",
        "hand_shape": "nine_hand",
        "path": "static_center",
        "hand_scale": 0.18,
    },
    "ten": {
        "label": "ten",
        "anchor": "shoulder_center",
        "hand_shape": "thumb_up",
        "path": "side_shake",
        "hand_scale": 0.17,
    },
    "blue": {
        "label": "blue",
        "anchor": "shoulder_center",
        "hand_shape": "b_hand",
        "path": "side_shake",
        "hand_scale": 0.18,
    },
    "green": {
        "label": "green",
        "anchor": "shoulder_center",
        "hand_shape": "g_hand",
        "path": "side_shake",
        "hand_scale": 0.17,
    },
    "yellow": {
        "label": "yellow",
        "anchor": "shoulder_center",
        "hand_shape": "y_hand",
        "path": "side_shake",
        "hand_scale": 0.18,
    },
    "white": {
        "label": "white",
        "anchor": "shoulder_center",
        "hand_shape": "open_spread",
        "path": "white_pull",
        "shape_motion": "white_release",
        "hand_scale": 0.18,
    },
    "happy": {
        "label": "happy",
        "anchor": "shoulder_center",
        "hand_shape": "open",
        "path": "happy_brush",
        "hand_scale": 0.17,
    },
    "angry": {
        "label": "angry",
        "anchor": "shoulder_center",
        "hand_shape": "claw_hand",
        "path": "angry_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "claw_hand",
        "secondary_path": "angry_secondary",
        "secondary_hand_scale": 0.17,
    },
    "tired": {
        "label": "tired",
        "anchor": "nose",
        "hand_shape": "two_finger_thumb_open",
        "path": "tired_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "two_finger_thumb_open",
        "secondary_path": "tired_secondary",
        "secondary_hand_scale": 0.17,
    },
    "eat": {
        "label": "eat",
        "anchor": "mouth",
        "hand_shape": "flat_o",
        "path": "eat_tap",
        "hand_scale": 0.17,
    },
    "drink": {
        "label": "drink",
        "anchor": "mouth",
        "hand_shape": "c_hand",
        "path": "drink_tilt",
        "hand_scale": 0.17,
    },
    "understand": {
        "label": "understand",
        "anchor": "forehead",
        "hand_shape": "fist",
        "path": "temple_flick",
        "shape_motion": "understand_flick",
        "hand_scale": 0.16,
    },
    "where": {
        "label": "where",
        "anchor": "mouth",
        "hand_shape": "index_point",
        "path": "question_shake",
        "hand_scale": 0.17,
    },
    "who": {
        "label": "who",
        "anchor": "mouth",
        "hand_shape": "index_point",
        "path": "who_circle",
        "hand_scale": 0.17,
    },
    "water": {
        "label": "water",
        "anchor": "chin",
        "hand_shape": "w_hand",
        "path": "chin_tap",
        "hand_scale": 0.18,
    },
    "maybe": {
        "label": "maybe",
        "anchor": "shoulder_center",
        "hand_shape": "open",
        "path": "maybe_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "open",
        "secondary_path": "maybe_secondary",
        "secondary_hand_scale": 0.17,
    },
    "what": {
        "label": "what",
        "anchor": "shoulder_center",
        "hand_shape": "open",
        "path": "what_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "open",
        "secondary_path": "what_secondary",
        "secondary_hand_scale": 0.17,
    },
    "more": {
        "label": "more",
        "anchor": "shoulder_center",
        "hand_shape": "flat_o",
        "path": "more_primary",
        "hand_scale": 0.16,
        "secondary_hand_shape": "flat_o",
        "secondary_path": "more_secondary",
        "secondary_hand_scale": 0.16,
    },
    "finished": {
        "label": "finished",
        "anchor": "shoulder_center",
        "hand_shape": "open_spread",
        "path": "finished_primary",
        "hand_scale": 0.18,
        "secondary_hand_shape": "open_spread",
        "secondary_path": "finished_secondary",
        "secondary_hand_scale": 0.18,
    },
    "help": {
        "label": "help",
        "anchor": "shoulder_center",
        "hand_shape": "thumb_up",
        "path": "help_primary",
        "hand_scale": 0.16,
        "secondary_hand_shape": "open",
        "secondary_path": "help_secondary",
        "secondary_hand_scale": 0.17,
    },
    "stop": {
        "label": "stop",
        "anchor": "shoulder_center",
        "hand_shape": "open",
        "path": "stop_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "open",
        "secondary_path": "stop_secondary",
        "secondary_hand_scale": 0.17,
    },
    "wait": {
        "label": "wait",
        "anchor": "shoulder_center",
        "hand_shape": "two_finger_thumb_open",
        "path": "wait_primary",
        "hand_scale": 0.16,
        "secondary_hand_shape": "open",
        "secondary_path": "wait_secondary",
        "secondary_hand_scale": 0.17,
    },
    "when": {
        "label": "when",
        "anchor": "mouth",
        "hand_shape": "index_point",
        "path": "when_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "index_point",
        "secondary_path": "when_secondary",
        "secondary_hand_scale": 0.17,
    },
    "how": {
        "label": "how",
        "anchor": "shoulder_center",
        "hand_shape": "fist",
        "path": "how_primary",
        "hand_scale": 0.16,
        "secondary_hand_shape": "fist",
        "secondary_path": "how_secondary",
        "secondary_hand_scale": 0.16,
    },
    "sad": {
        "label": "sad",
        "anchor": "mouth",
        "hand_shape": "open_spread",
        "path": "sad_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "open_spread",
        "secondary_path": "sad_secondary",
        "secondary_hand_scale": 0.17,
    },
    "love": {
        "label": "love",
        "anchor": "shoulder_center",
        "hand_shape": "open",
        "path": "love_primary",
        "hand_scale": 0.17,
        "secondary_hand_shape": "open",
        "secondary_path": "love_secondary",
        "secondary_hand_scale": 0.17,
    },
}

SYNTHETIC_TEMPLATE_SIGNS = tuple(TEMPLATE_PROFILES.keys())


def has_template_support(sign_name: str) -> bool:
    sign = normalize_sign_name(sign_name)
    return get_template_path(sign).exists() or sign in SYNTHETIC_TEMPLATE_SIGNS


def get_template_path(sign_name: str) -> Path:
    return TEMPLATE_DIR / f"{normalize_sign_name(sign_name)}.json"


def ensure_template_file(sign_name: str, *, overwrite: bool = False) -> Path:
    sign = normalize_sign_name(sign_name)
    if sign not in TEMPLATE_PROFILES:
        raise FileNotFoundError(f"No supported template is configured for '{sign}'.")

    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    template_path = get_template_path(sign)
    if template_path.exists() and not overwrite:
        return template_path

    template_payload = build_synthetic_template(sign)
    template_path.write_text(json.dumps(template_payload, indent=2), encoding="utf-8")
    return template_path


def load_template(sign_name: str) -> dict:
    sign = normalize_sign_name(sign_name)
    template_path = ensure_template_file(sign)
    return json.loads(template_path.read_text(encoding="utf-8"))


def build_synthetic_template(sign_name: str, frame_count: int = DEFAULT_TARGET_FRAME_COUNT) -> dict:
    sign = normalize_sign_name(sign_name)
    profile = TEMPLATE_PROFILES[sign]
    anchors = DEFAULT_BODY_ANCHORS
    wrist_path = _build_wrist_path(profile["path"], frame_count)
    hand_shapes = _build_shape_sequence(profile, frame_count)
    hand_scale = profile["hand_scale"]
    secondary_wrist_path = None
    secondary_hand_shapes = None
    secondary_hand_scale = profile.get("secondary_hand_scale")

    if profile.get("secondary_path") and profile.get("secondary_hand_shape"):
        secondary_wrist_path = _build_wrist_path(profile["secondary_path"], frame_count)
        secondary_hand_shapes = _build_shape_sequence(
            {
                "hand_shape": profile["secondary_hand_shape"],
                "shape_motion": profile.get("secondary_shape_motion", "static"),
            },
            frame_count,
        )

    frames = []
    for index, (wrist, hand_shape) in enumerate(zip(wrist_path, hand_shapes)):
        hand_landmarks = (hand_shape * hand_scale) + wrist
        frame_anchors = {
            key: value.tolist() if hasattr(value, "tolist") else float(value)
            for key, value in anchors.items()
        }
        frame_payload = {
            "handedness": "right",
            "hand_landmarks": hand_landmarks.tolist(),
            "hand_center": hand_landmarks.mean(axis=0).tolist(),
            "openness": float(_compute_openness(hand_landmarks)),
            "palm_size": float(_compute_palm_size(hand_landmarks)),
            "scale_hint": float(anchors["scale_hint"]),
            "anchors": frame_anchors,
        }

        if secondary_wrist_path is not None and secondary_hand_shapes is not None and secondary_hand_scale is not None:
            secondary_hand_landmarks = _orient_shape(secondary_hand_shapes[index], side="left") * secondary_hand_scale + secondary_wrist_path[index]
            frame_payload.update(
                {
                    "secondary_handedness": "left",
                    "secondary_hand_landmarks": secondary_hand_landmarks.tolist(),
                    "secondary_hand_center": secondary_hand_landmarks.mean(axis=0).tolist(),
                    "secondary_openness": float(_compute_openness(secondary_hand_landmarks)),
                    "secondary_palm_size": float(_compute_palm_size(secondary_hand_landmarks)),
                }
            )

        frames.append(frame_payload)

    return {
        "sequence_version": 1,
        "exercise": sign,
        "source": "synthetic_default",
        "profile": profile,
        "frame_count_original": frame_count,
        "usable_frame_count": frame_count,
        "resampled_frame_count": frame_count,
        "handedness": "right",
        "frames": frames,
    }


def save_template_from_video(sign_name: str, video_path: str | Path, *, overwrite: bool = False) -> Path:
    sign = normalize_sign_name(sign_name)
    sequence = extract_landmark_sequence_from_video(video_path, target_frames=DEFAULT_TARGET_FRAME_COUNT)
    if not sequence["frames"]:
        raise RuntimeError(f"No landmarks were detected in the reference video for '{sign}'.")

    template_payload = {
        **sequence,
        "exercise": sign,
        "source": str(video_path),
        "profile": TEMPLATE_PROFILES.get(sign, {"label": sign, "anchor": "shoulder_center"}),
    }
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    template_path = get_template_path(sign)
    if template_path.exists() and not overwrite:
        raise FileExistsError(f"Template already exists for '{sign}'. Use --overwrite to replace it.")
    template_path.write_text(json.dumps(template_payload, indent=2), encoding="utf-8")
    return template_path


def compare_video_to_template(video_source, sign_name: str, *, passing_score: float = 70.0) -> dict:
    user_sequence = extract_landmark_sequence_from_video(video_source, target_frames=DEFAULT_TARGET_FRAME_COUNT)
    template = load_template(sign_name)
    comparison = compare_sequence_to_template(
        user_sequence=user_sequence,
        template=template,
        passing_score=passing_score,
    )
    comparison["template_path"] = str(get_template_path(sign_name))
    return comparison


def compare_sequence_to_template(user_sequence: dict, template: dict, *, passing_score: float = 70.0) -> dict:
    sign = normalize_sign_name(template.get("exercise") or template.get("profile", {}).get("label") or "")
    user_frames = user_sequence.get("frames") or []
    template_frames = template.get("frames") or []

    if not user_frames:
        return {
            "exercise": sign,
            "score": 0.0,
            "correct": False,
            "shape_score": 0.0,
            "position_score": 0.0,
            "motion_score": 0.0,
            "metrics": {
                "usable_frames": 0,
                "start_anchor_distance": 1.0,
                "end_anchor_distance": 1.0,
                "motion_direction_alignment": 0.0,
                "motion_magnitude_ratio": 0.0,
                "path_efficiency": 0.0,
                "hand_openness": 0.0,
                "template_hand_openness": 0.0,
                "horizontal_displacement": 0.0,
                "vertical_displacement": 0.0,
            },
            "tracking_data": {
                "frames_received": user_sequence.get("frame_count_original", 0),
                "frames_with_landmarks": 0,
                "frames_compared": len(template_frames),
            },
        }

    target_frame_count = len(template_frames) or DEFAULT_TARGET_FRAME_COUNT
    user_frames = _resample_sequence_frames(user_frames, target_frame_count)
    template_frames = _resample_sequence_frames(template_frames, target_frame_count)

    profile = template.get("profile", {})
    anchor_name = profile.get("anchor", "shoulder_center")
    user_shape = _shape_features(user_frames)
    template_shape = _shape_features(template_frames)
    user_position = _position_features(user_frames, anchor_name)
    template_position = _position_features(template_frames, anchor_name)
    user_motion = np.diff(user_position, axis=0)
    template_motion = np.diff(template_position, axis=0)

    shape_score = _distance_to_score(_mean_frame_distance(user_shape, template_shape), scale=1.15)
    position_score = _distance_to_score(_mean_frame_distance(user_position, template_position), scale=0.85)
    motion_score = _distance_to_score(_mean_frame_distance(user_motion, template_motion), scale=0.22)

    template_has_secondary = any("secondary_hand_landmarks" in frame for frame in template_frames)
    user_has_secondary = any("secondary_hand_landmarks" in frame for frame in user_frames)

    if template_has_secondary:
        if user_has_secondary:
            user_secondary_shape = _shape_features(user_frames, prefix="secondary_")
            template_secondary_shape = _shape_features(template_frames, prefix="secondary_")
            user_secondary_position = _position_features(user_frames, anchor_name, prefix="secondary_")
            template_secondary_position = _position_features(template_frames, anchor_name, prefix="secondary_")
            user_secondary_motion = np.diff(user_secondary_position, axis=0)
            template_secondary_motion = np.diff(template_secondary_position, axis=0)
            secondary_shape_score = _distance_to_score(
                _mean_frame_distance(user_secondary_shape, template_secondary_shape),
                scale=1.15,
            )
            secondary_position_score = _distance_to_score(
                _mean_frame_distance(user_secondary_position, template_secondary_position),
                scale=0.85,
            )
            secondary_motion_score = _distance_to_score(
                _mean_frame_distance(user_secondary_motion, template_secondary_motion),
                scale=0.22,
            )
            pair_shape_score = round((shape_score + secondary_shape_score) / 2.0, 1)
            pair_position_score = round((position_score + secondary_position_score) / 2.0, 1)
            pair_motion_score = round((motion_score + secondary_motion_score) / 2.0, 1)
        else:
            pair_shape_score = round(shape_score / 2.0, 1)
            pair_position_score = round(position_score / 2.0, 1)
            pair_motion_score = round(motion_score / 2.0, 1)
        shape_score, position_score, motion_score = pair_shape_score, pair_position_score, pair_motion_score

    final_score = round(
        (SHAPE_SCORE_WEIGHT * shape_score)
        + (POSITION_SCORE_WEIGHT * position_score)
        + (MOTION_SCORE_WEIGHT * motion_score),
        1,
    )

    net_user_motion = user_position[-1] - user_position[0]
    net_template_motion = template_position[-1] - template_position[0]
    motion_direction_alignment = _cosine_similarity(net_user_motion, net_template_motion)
    template_magnitude = float(np.linalg.norm(net_template_motion))
    user_magnitude = float(np.linalg.norm(net_user_motion))
    motion_magnitude_ratio = user_magnitude / max(template_magnitude, 1e-6)
    path_efficiency = _path_efficiency(user_position)
    start_anchor_distance = float(np.linalg.norm(user_position[0] - template_position[0]))
    end_anchor_distance = float(np.linalg.norm(user_position[-1] - template_position[-1]))

    hand_openness = float(np.mean([frame["openness"] for frame in user_frames]))
    template_hand_openness = float(np.mean([frame["openness"] for frame in template_frames]))
    horizontal_displacement = float(abs(net_user_motion[0]))
    vertical_displacement = float(abs(net_user_motion[1]))
    min_required_frames = min(8, target_frame_count)
    component_floors_met = shape_score >= 45.0 and position_score >= 40.0 and motion_score >= 35.0
    correct = (
        final_score >= passing_score
        and component_floors_met
        and user_sequence.get("usable_frame_count", 0) >= min_required_frames
    )

    return {
        "exercise": sign,
        "score": final_score,
        "correct": correct,
        "shape_score": shape_score,
        "position_score": position_score,
        "motion_score": motion_score,
        "metrics": {
            "usable_frames": user_sequence.get("usable_frame_count", 0),
            "start_anchor_distance": round(start_anchor_distance, 4),
            "end_anchor_distance": round(end_anchor_distance, 4),
            "motion_direction_alignment": round(motion_direction_alignment, 4),
            "motion_magnitude_ratio": round(motion_magnitude_ratio, 4),
            "path_efficiency": round(path_efficiency, 4),
            "hand_openness": round(hand_openness, 4),
            "template_hand_openness": round(template_hand_openness, 4),
            "horizontal_displacement": round(horizontal_displacement, 4),
            "vertical_displacement": round(vertical_displacement, 4),
            "secondary_required": template_has_secondary,
            "secondary_detected": user_has_secondary,
        },
        "tracking_data": {
            "frames_received": user_sequence.get("frame_count_original", 0),
            "frames_with_landmarks": user_sequence.get("usable_frame_count", 0),
            "frames_with_secondary_landmarks": user_sequence.get("secondary_usable_frame_count", 0),
            "frames_compared": target_frame_count,
            "anchor_name": anchor_name,
            "shape_score": shape_score,
            "position_score": position_score,
            "motion_score": motion_score,
        },
    }


def _build_wrist_path(path_name: str, frame_count: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, num=frame_count, dtype=np.float32)
    if path_name == "static_center":
        x = np.full_like(t, 0.55)
        y = np.full_like(t, 0.50)
    elif path_name == "hello_wave":
        x = 0.55 + (0.17 * t)
        y = 0.28 + (0.03 * t)
    elif path_name == "goodbye_wave":
        x = 0.66 + (0.02 * np.sin(2.5 * np.pi * t))
        y = 0.33 + (0.01 * np.sin(5.0 * np.pi * t))
    elif path_name == "thank_you_release":
        x = 0.51 + (0.18 * t)
        y = 0.43 + (0.10 * t)
    elif path_name == "yes_bob":
        x = np.full_like(t, 0.58)
        y = 0.56 + (0.05 * np.sin(2.5 * np.pi * t))
    elif path_name == "chest_circle":
        x = 0.56 + (0.05 * np.cos(2.0 * np.pi * t))
        y = 0.60 + (0.05 * np.sin(2.0 * np.pi * t))
    elif path_name == "small_chest_circle":
        x = 0.56 + (0.04 * np.cos(2.0 * np.pi * t))
        y = 0.60 + (0.04 * np.sin(2.0 * np.pi * t))
    elif path_name == "chin_tap":
        x = np.full_like(t, 0.53)
        y = 0.42 + (0.018 * np.sin(4.0 * np.pi * t))
    elif path_name == "forehead_tap":
        x = np.full_like(t, 0.53)
        y = 0.25 + (0.018 * np.sin(4.0 * np.pi * t))
    elif path_name == "brother_primary":
        x = 0.56 - (0.06 * t)
        y = 0.25 + (0.24 * t)
    elif path_name == "brother_secondary":
        x = np.full_like(t, 0.45)
        y = np.full_like(t, 0.49)
    elif path_name == "sister_primary":
        x = 0.56 - (0.06 * t)
        y = 0.42 + (0.12 * t)
    elif path_name == "sister_secondary":
        x = np.full_like(t, 0.45)
        y = np.full_like(t, 0.54)
    elif path_name == "friend_primary":
        x = 0.58 - (0.08 * t)
        y = 0.52 + (0.02 * np.sin(np.pi * t))
    elif path_name == "friend_secondary":
        x = 0.42 + (0.08 * t)
        y = 0.52 + (0.02 * np.sin(np.pi * t))
    elif path_name == "mouth_brush_down":
        x = 0.47 + (0.02 * t)
        y = 0.35 + (0.12 * t)
    elif path_name == "forehead_slide":
        x = 0.41 + (0.18 * t)
        y = np.full_like(t, 0.24)
    elif path_name == "no_snap":
        x = 0.49 + (0.03 * np.sin(4.0 * np.pi * t))
        y = np.full_like(t, 0.37)
    elif path_name == "side_shake":
        x = 0.55 + (0.05 * np.sin(4.0 * np.pi * t))
        y = np.full_like(t, 0.48)
    elif path_name == "white_pull":
        x = 0.54 + (0.09 * t)
        y = 0.58 - (0.03 * t)
    elif path_name == "happy_brush":
        x = 0.55 + (0.03 * np.cos(4.0 * np.pi * t))
        y = 0.64 - (0.10 * t) + (0.015 * np.sin(4.0 * np.pi * t))
    elif path_name == "angry_primary":
        x = 0.58 + (0.02 * t)
        y = 0.74 - (0.15 * t)
    elif path_name == "angry_secondary":
        x = 0.42 - (0.02 * t)
        y = 0.74 - (0.15 * t)
    elif path_name == "tired_primary":
        x = 0.55 + (0.01 * t)
        y = 0.33 + (0.27 * t)
    elif path_name == "tired_secondary":
        x = 0.45 - (0.01 * t)
        y = 0.33 + (0.27 * t)
    elif path_name == "eat_tap":
        x = np.full_like(t, 0.51)
        y = 0.40 + (0.02 * np.sin(4.0 * np.pi * t))
    elif path_name == "drink_tilt":
        x = 0.53 + (0.025 * np.sin(2.0 * np.pi * t))
        y = 0.41 - (0.03 * np.maximum(0.0, np.sin(np.pi * t)))
    elif path_name == "temple_flick":
        x = 0.54 + (0.06 * t)
        y = 0.28 - (0.03 * t)
    elif path_name == "question_shake":
        x = 0.55 + (0.05 * np.sin(4.0 * np.pi * t))
        y = np.full_like(t, 0.38)
    elif path_name == "who_circle":
        x = 0.52 + (0.04 * np.cos(2.0 * np.pi * t))
        y = 0.37 + (0.04 * np.sin(2.0 * np.pi * t))
    elif path_name == "maybe_primary":
        x = np.full_like(t, 0.60)
        y = 0.53 + (0.04 * np.sin(2.0 * np.pi * t))
    elif path_name == "maybe_secondary":
        x = np.full_like(t, 0.42)
        y = 0.53 - (0.04 * np.sin(2.0 * np.pi * t))
    elif path_name == "what_primary":
        x = 0.60 + (0.03 * np.sin(4.0 * np.pi * t))
        y = np.full_like(t, 0.57)
    elif path_name == "what_secondary":
        x = 0.40 - (0.03 * np.sin(4.0 * np.pi * t))
        y = np.full_like(t, 0.57)
    elif path_name == "more_primary":
        x = 0.61 - (0.10 * np.maximum(0.0, np.sin(2.0 * np.pi * t)))
        y = np.full_like(t, 0.56)
    elif path_name == "more_secondary":
        x = 0.39 + (0.10 * np.maximum(0.0, np.sin(2.0 * np.pi * t)))
        y = np.full_like(t, 0.56)
    elif path_name == "finished_primary":
        x = 0.58 + (0.08 * t)
        y = 0.50 - (0.03 * t)
    elif path_name == "finished_secondary":
        x = 0.42 - (0.08 * t)
        y = 0.50 - (0.03 * t)
    elif path_name == "help_primary":
        x = np.full_like(t, 0.55)
        y = 0.50 - (0.10 * t)
    elif path_name == "help_secondary":
        x = np.full_like(t, 0.50)
        y = 0.56 - (0.10 * t)
    elif path_name == "stop_primary":
        x = np.full_like(t, 0.56)
        y = 0.44 + (0.14 * t)
    elif path_name == "stop_secondary":
        x = np.full_like(t, 0.48)
        y = np.full_like(t, 0.58)
    elif path_name == "wait_primary":
        x = np.full_like(t, 0.56)
        y = 0.50 + (0.08 * np.maximum(0.0, np.sin(3.0 * np.pi * t)))
    elif path_name == "wait_secondary":
        x = np.full_like(t, 0.47)
        y = np.full_like(t, 0.58)
    elif path_name == "when_primary":
        x = np.full_like(t, 0.47)
        y = np.full_like(t, 0.38)
    elif path_name == "when_secondary":
        x = 0.54 + (0.04 * np.cos(2.0 * np.pi * t))
        y = 0.38 + (0.04 * np.sin(2.0 * np.pi * t))
    elif path_name == "how_primary":
        x = 0.52 - (0.06 * t)
        y = 0.56 - (0.05 * t)
    elif path_name == "how_secondary":
        x = 0.48 + (0.06 * t)
        y = 0.56 - (0.05 * t)
    elif path_name == "sad_primary":
        x = 0.58 - (0.03 * t)
        y = 0.32 + (0.22 * t)
    elif path_name == "sad_secondary":
        x = 0.42 + (0.03 * t)
        y = 0.32 + (0.22 * t)
    elif path_name == "love_primary":
        x = 0.63 - (0.14 * t)
        y = 0.52 + (0.10 * t)
    elif path_name == "love_secondary":
        x = 0.37 + (0.14 * t)
        y = 0.52 + (0.10 * t)
    else:
        x = np.full_like(t, 0.55)
        y = np.full_like(t, 0.50)
    z = np.zeros_like(t)
    return np.stack([x, y, z], axis=1)


def _build_shape_sequence(profile: dict, frame_count: int) -> np.ndarray:
    base_shape = CANONICAL_HAND_SHAPES[profile["hand_shape"]]
    shape_motion = profile.get("shape_motion", "static")
    if shape_motion == "static":
        return np.repeat(base_shape[None, ...], frame_count, axis=0)

    t = np.linspace(0.0, 1.0, num=frame_count, dtype=np.float32)
    if shape_motion == "goodbye_wave":
        open_shape = CANONICAL_HAND_SHAPES["open_spread"]
        closed_shape = CANONICAL_HAND_SHAPES["goodbye_closed"]
        factors = (np.sin(5.0 * np.pi * t) + 1.0) / 2.0
        return np.stack([_blend_shapes(closed_shape, open_shape, factor) for factor in factors], axis=0)
    if shape_motion == "no_snap":
        open_shape = CANONICAL_HAND_SHAPES["two_finger_thumb_open"]
        closed_shape = CANONICAL_HAND_SHAPES["two_finger_thumb_closed"]
        factors = (np.sin(4.0 * np.pi * t) + 1.0) / 2.0
        return np.stack([_blend_shapes(closed_shape, open_shape, factor) for factor in factors], axis=0)
    if shape_motion == "white_release":
        open_shape = CANONICAL_HAND_SHAPES["open_spread"]
        closed_shape = CANONICAL_HAND_SHAPES["flat_o"]
        factors = np.clip(t * 1.2, 0.0, 1.0)
        return np.stack([_blend_shapes(open_shape, closed_shape, factor) for factor in factors], axis=0)
    if shape_motion == "understand_flick":
        closed_shape = CANONICAL_HAND_SHAPES["fist"]
        open_shape = CANONICAL_HAND_SHAPES["index_point"]
        factors = np.clip((t - 0.35) / 0.45, 0.0, 1.0)
        return np.stack([_blend_shapes(closed_shape, open_shape, factor) for factor in factors], axis=0)

    return np.repeat(base_shape[None, ...], frame_count, axis=0)


def _blend_shapes(start: np.ndarray, end: np.ndarray, factor: float) -> np.ndarray:
    return ((1.0 - factor) * start) + (factor * end)


def _orient_shape(shape: np.ndarray, side: str) -> np.ndarray:
    if side != "left":
        return np.array(shape, copy=True)
    oriented = np.array(shape, copy=True)
    oriented[:, 0] *= -1.0
    return oriented


def _compute_palm_size(hand_landmarks: np.ndarray) -> float:
    palm_span = float(np.linalg.norm(hand_landmarks[17, :2] - hand_landmarks[5, :2]))
    palm_height = float(np.linalg.norm(hand_landmarks[9, :2] - hand_landmarks[0, :2]))
    return max(palm_span, palm_height, 1e-6)


def _compute_openness(hand_landmarks: np.ndarray) -> float:
    wrist = hand_landmarks[0, :2]
    palm_size = _compute_palm_size(hand_landmarks)
    tips = (4, 8, 12, 16, 20)
    return float(np.mean([np.linalg.norm(hand_landmarks[index, :2] - wrist) for index in tips]) / palm_size)


def _shape_features(frames: list[dict], prefix: str = "") -> np.ndarray:
    hand_key = f"{prefix}hand_landmarks"
    openness_key = f"{prefix}openness"
    palm_size_key = f"{prefix}palm_size"
    features = []
    for frame in frames:
        hand = np.array(frame[hand_key], dtype=np.float32)
        wrist = hand[0, :2]
        palm_size = max(float(frame.get(palm_size_key) or _compute_palm_size(hand)), 1e-6)
        x_flip = -1.0 if hand[5, 0] > hand[17, 0] else 1.0

        def extension(tip_index: int, mcp_index: int) -> float:
            tip = hand[tip_index, :2].copy()
            mcp = hand[mcp_index, :2].copy()
            tip[0] *= x_flip
            mcp[0] *= x_flip
            adjusted_wrist = wrist.copy()
            adjusted_wrist[0] *= x_flip
            return float(np.linalg.norm(tip - adjusted_wrist) / max(np.linalg.norm(mcp - adjusted_wrist), 1e-6))

        thumb_extension = extension(4, 2)
        index_extension = extension(8, 5)
        middle_extension = extension(12, 9)
        ring_extension = extension(16, 13)
        pinky_extension = extension(20, 17)

        index_middle_spread = float(np.linalg.norm(hand[8, :2] - hand[12, :2]) / palm_size)
        middle_ring_spread = float(np.linalg.norm(hand[12, :2] - hand[16, :2]) / palm_size)
        ring_pinky_spread = float(np.linalg.norm(hand[16, :2] - hand[20, :2]) / palm_size)

        features.append(
            [
                thumb_extension,
                index_extension,
                middle_extension,
                ring_extension,
                pinky_extension,
                index_middle_spread,
                middle_ring_spread,
                ring_pinky_spread,
                float(frame.get(openness_key, _compute_openness(hand))),
            ]
        )
    return np.array(features, dtype=np.float32)


def _position_features(frames: list[dict], anchor_name: str, prefix: str = "") -> np.ndarray:
    center_key = f"{prefix}hand_center"
    positions = []
    for frame in frames:
        hand_center = np.array(frame[center_key], dtype=np.float32)
        anchors = frame["anchors"]
        anchor = np.array(anchors[anchor_name], dtype=np.float32)
        scale_hint = max(float(frame.get("scale_hint") or anchors.get("scale_hint") or 1.0), 1e-6)
        delta = hand_center - anchor
        positions.append(
            [
                abs(float(delta[0])) / scale_hint,
                float(delta[1]) / scale_hint,
                float(delta[2]),
            ]
        )
    return np.array(positions, dtype=np.float32)


def _resample_sequence_frames(frames: list[dict], target_frames: int) -> list[dict]:
    if len(frames) == target_frames:
        return frames

    indices = np.linspace(0, len(frames) - 1, num=target_frames)
    lower = np.floor(indices).astype(int)
    upper = np.ceil(indices).astype(int)
    weights = indices - lower

    interpolated_frames = []
    for position, start_index, end_index in zip(weights, lower, upper):
        start = frames[start_index]
        end = frames[end_index]
        if start_index == end_index:
            interpolated_frames.append(start)
            continue
        interpolated_frames.append(
            {
                "handedness": start.get("handedness") or end.get("handedness"),
                "hand_landmarks": _lerp_array(start["hand_landmarks"], end["hand_landmarks"], position).tolist(),
                "hand_center": _lerp_array(start["hand_center"], end["hand_center"], position).tolist(),
                "openness": float(_lerp_scalar(start["openness"], end["openness"], position)),
                "palm_size": float(_lerp_scalar(start["palm_size"], end["palm_size"], position)),
                "scale_hint": float(_lerp_scalar(start["scale_hint"], end["scale_hint"], position)),
                "anchors": {
                    key: _lerp_array(start["anchors"][key], end["anchors"][key], position).tolist()
                    if key != "scale_hint"
                    else float(_lerp_scalar(start["anchors"][key], end["anchors"][key], position))
                    for key in start["anchors"].keys()
                },
            }
            | (
                {
                    "secondary_handedness": start.get("secondary_handedness") or end.get("secondary_handedness"),
                    "secondary_hand_landmarks": _lerp_array(
                        start["secondary_hand_landmarks"],
                        end["secondary_hand_landmarks"],
                        position,
                    ).tolist(),
                    "secondary_hand_center": _lerp_array(
                        start["secondary_hand_center"],
                        end["secondary_hand_center"],
                        position,
                    ).tolist(),
                    "secondary_openness": float(
                        _lerp_scalar(start["secondary_openness"], end["secondary_openness"], position)
                    ),
                    "secondary_palm_size": float(
                        _lerp_scalar(start["secondary_palm_size"], end["secondary_palm_size"], position)
                    ),
                }
                if "secondary_hand_landmarks" in start and "secondary_hand_landmarks" in end
                else {}
            )
        )
    return interpolated_frames


def _lerp_array(start, end, weight):
    return ((1.0 - weight) * np.array(start, dtype=np.float32)) + (weight * np.array(end, dtype=np.float32))


def _lerp_scalar(start, end, weight):
    return ((1.0 - weight) * float(start)) + (weight * float(end))


def _mean_frame_distance(left: np.ndarray, right: np.ndarray) -> float:
    if left.size == 0 or right.size == 0:
        return 1.0
    return float(np.mean(np.linalg.norm(left - right, axis=-1)))


def _distance_to_score(distance: float, *, scale: float) -> float:
    return round(max(0.0, min(100.0, 100.0 * (1.0 - (distance / max(scale, 1e-6))))), 1)


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm < 1e-6 or right_norm < 1e-6:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _path_efficiency(position_sequence: np.ndarray) -> float:
    if len(position_sequence) < 2:
        return 0.0
    step_lengths = np.linalg.norm(np.diff(position_sequence, axis=0), axis=1)
    total_length = float(np.sum(step_lengths))
    if total_length < 1e-6:
        return 0.0
    net_displacement = float(np.linalg.norm(position_sequence[-1] - position_sequence[0]))
    return net_displacement / total_length
