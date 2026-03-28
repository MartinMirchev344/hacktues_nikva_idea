from __future__ import annotations

from .compare import TEMPLATE_PROFILES
from .mediapipe_utils import normalize_sign_name


def build_exercise_feedback(sign_name: str, comparison: dict) -> tuple[str, list[str]]:
    sign = normalize_sign_name(sign_name)
    profile = TEMPLATE_PROFILES.get(sign, {"label": sign.replace("_", " ")})
    label = profile["label"]
    metrics = comparison.get("metrics", {})
    score = comparison.get("score", 0.0)
    correct = comparison.get("correct", False)

    if metrics.get("usable_frames", 0) == 0:
        return (
            "Your hands were not visible clearly enough to score this sign.",
            [
                "Keep your hand and upper body fully inside the frame.",
                "Use brighter lighting so MediaPipe can track your hand landmarks.",
            ],
        )

    feedback_items = []

    if metrics.get("secondary_required") and not metrics.get("secondary_detected"):
        feedback_items.append("Keep both hands clearly visible in the frame for this sign.")

    if sign == "hello":
        if metrics.get("start_anchor_distance", 0.0) > 0.42:
            feedback_items.append("Raise your hand closer to your forehead before you start the sign.")
        if metrics.get("motion_direction_alignment", 1.0) < 0.45 or metrics.get("motion_magnitude_ratio", 1.0) < 0.7:
            feedback_items.append("Make the outward hello motion clearer and a little larger.")
        if metrics.get("hand_openness", 0.0) < max(metrics.get("template_hand_openness", 0.0) - 0.22, 1.45):
            feedback_items.append("Keep your hand more open with the fingers extended.")
    elif sign == "thank_you":
        if metrics.get("start_anchor_distance", 0.0) > 0.38:
            feedback_items.append("Start with your fingertips closer to your chin or mouth.")
        if metrics.get("motion_direction_alignment", 1.0) < 0.45 or metrics.get("motion_magnitude_ratio", 1.0) < 0.7:
            feedback_items.append("Move your hand outward from the chin more clearly.")
        if metrics.get("path_efficiency", 1.0) < 0.55:
            feedback_items.append("Keep the forward movement smoother instead of adding extra wobble.")
    elif sign == "yes":
        if metrics.get("hand_openness", 0.0) > min(metrics.get("template_hand_openness", 0.0) + 0.22, 1.8):
            feedback_items.append("Close your hand into a firmer fist for the yes sign.")
        if metrics.get("vertical_displacement", 0.0) < 0.18:
            feedback_items.append("Bob your fist up and down more clearly, like a nod.")
        if metrics.get("horizontal_displacement", 0.0) > metrics.get("vertical_displacement", 0.0) * 0.9:
            feedback_items.append("Keep the motion compact and mostly vertical instead of drifting sideways.")
    elif sign == "goodbye":
        if metrics.get("start_anchor_distance", 0.0) > 0.42:
            feedback_items.append("Start the goodbye sign higher, near the side of your face.")
        if metrics.get("motion_score", 0.0) < 62.0 or metrics.get("path_efficiency", 1.0) > 0.9:
            feedback_items.append("Open and close the hand more clearly to show the goodbye wave.")
        if metrics.get("hand_openness", 0.0) < 1.6:
            feedback_items.append("Keep the fingers more spread when the hand opens.")
    elif sign == "please":
        if metrics.get("start_anchor_distance", 0.0) > 0.40:
            feedback_items.append("Place your flat hand on the center of your chest before moving.")
        if metrics.get("motion_score", 0.0) < 65.0:
            feedback_items.append("Make the circular motion on your chest smoother and more complete.")
        if metrics.get("hand_openness", 0.0) < 1.45:
            feedback_items.append("Keep the hand flatter instead of curling the fingers.")
    elif sign == "sorry":
        if metrics.get("start_anchor_distance", 0.0) > 0.40:
            feedback_items.append("Keep your fist in contact with the center of your chest.")
        if metrics.get("motion_score", 0.0) < 65.0:
            feedback_items.append("Rub the fist in a clearer circle on your chest.")
        if metrics.get("hand_openness", 0.0) > 1.55:
            feedback_items.append("Close your hand into a tighter fist for the sign sorry.")
    elif sign == "no":
        if metrics.get("start_anchor_distance", 0.0) > 0.38:
            feedback_items.append("Start the no sign closer to your mouth or chin.")
        if metrics.get("motion_score", 0.0) < 62.0:
            feedback_items.append("Snap the index and middle fingers toward the thumb more clearly.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Keep the index and middle fingers together with the thumb ready to close.")
    elif sign == "mother":
        if metrics.get("start_anchor_distance", 0.0) > 0.34:
            feedback_items.append("Bring your thumb to the chin for the mother sign.")
        if metrics.get("hand_openness", 0.0) < 1.6:
            feedback_items.append("Spread the fingers wider while keeping the hand open.")
        if metrics.get("motion_score", 0.0) < 60.0:
            feedback_items.append("Tap the chin more clearly instead of holding the hand still.")
    elif sign == "father":
        if metrics.get("start_anchor_distance", 0.0) > 0.34:
            feedback_items.append("Raise your thumb to the forehead for the father sign.")
        if metrics.get("hand_openness", 0.0) < 1.6:
            feedback_items.append("Spread the fingers wider while keeping the hand open.")
        if metrics.get("motion_score", 0.0) < 60.0:
            feedback_items.append("Tap the forehead more clearly instead of holding the hand still.")
    elif sign == "brother":
        if metrics.get("start_anchor_distance", 0.0) > 0.36:
            feedback_items.append("Start the brother sign with the thumb side higher near the forehead.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Bring the dominant hand down to meet the other hand more clearly for brother.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Use a clearer L handshape with the thumb and index finger open.")
    elif sign == "sister":
        if metrics.get("start_anchor_distance", 0.0) > 0.36:
            feedback_items.append("Start the sister sign with the thumb side closer to your chin.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Bring the dominant hand down to meet the other hand more clearly for sister.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Use a clearer L handshape with the thumb and index finger open.")
    elif sign == "friend":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Hook the index fingers together and switch them more clearly for friend.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Curve both index fingers into clearer hooked handshapes.")
        if metrics.get("position_score", 0.0) < 58.0:
            feedback_items.append("Keep both hands in front of your chest while the fingers link.")
    elif sign == "red":
        if metrics.get("start_anchor_distance", 0.0) > 0.36:
            feedback_items.append("Start with your index finger closer to your lips.")
        if metrics.get("motion_direction_alignment", 1.0) < 0.45 or metrics.get("vertical_displacement", 0.0) < 0.20:
            feedback_items.append("Brush the index finger downward more clearly for red.")
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Use a clearer pointing handshape with the index finger extended.")
    elif sign == "black":
        if metrics.get("start_anchor_distance", 0.0) > 0.36:
            feedback_items.append("Start the black sign with your index finger near the forehead.")
        if metrics.get("motion_direction_alignment", 1.0) < 0.45 or metrics.get("horizontal_displacement", 0.0) < 0.20:
            feedback_items.append("Slide the index finger across the forehead more clearly.")
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Use a clearer pointing handshape with the index finger extended.")
    elif sign == "one":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Raise only the index finger for the number one.")
        if metrics.get("hand_openness", 0.0) > 1.75:
            feedback_items.append("Fold the other fingers down more tightly.")
    elif sign == "two":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Raise the index and middle fingers clearly in a V shape for two.")
        if metrics.get("hand_openness", 0.0) < 1.55:
            feedback_items.append("Spread the two raised fingers a little more.")
    elif sign == "three":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Show the thumb, index, and middle fingers for the number three.")
        if metrics.get("hand_openness", 0.0) < 1.65:
            feedback_items.append("Keep the three visible fingers more open and clear.")
    elif sign == "four":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Raise four fingers while keeping the thumb tucked for four.")
        if metrics.get("hand_openness", 0.0) < 1.85:
            feedback_items.append("Spread the four raised fingers more evenly.")
    elif sign == "five":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Open all five fingers fully for the number five.")
        if metrics.get("hand_openness", 0.0) < 2.0:
            feedback_items.append("Spread the fingers wider so the hand looks fully open.")
    elif sign == "six":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Touch the thumb and pinky together for the number six.")
        if metrics.get("hand_openness", 0.0) < 1.8:
            feedback_items.append("Keep the other three fingers extended while the pinky meets the thumb.")
    elif sign == "seven":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Touch the thumb and ring finger together for the number seven.")
        if metrics.get("hand_openness", 0.0) < 1.8:
            feedback_items.append("Keep the remaining fingers extended and easy to read.")
    elif sign == "eight":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Touch the thumb and middle finger together for the number eight.")
        if metrics.get("hand_openness", 0.0) < 1.75:
            feedback_items.append("Keep the index, ring, and pinky fingers more clearly extended.")
    elif sign == "nine":
        if metrics.get("shape_score", 0.0) < 65.0:
            feedback_items.append("Touch the thumb and index finger together for the number nine.")
        if metrics.get("hand_openness", 0.0) < 1.65:
            feedback_items.append("Keep the other fingers up and separated a bit more.")
    elif sign == "ten":
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Hold the thumb up clearly while the other fingers stay closed.")
        if metrics.get("horizontal_displacement", 0.0) < 0.14:
            feedback_items.append("Shake the hand slightly from side to side for ten.")
    elif sign == "blue":
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Use a clearer B handshape with four fingers up and the thumb tucked.")
        if metrics.get("horizontal_displacement", 0.0) < 0.14:
            feedback_items.append("Shake the B handshape slightly for blue.")
    elif sign == "green":
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Use a clearer G handshape with the index finger and thumb extended sideways.")
        if metrics.get("horizontal_displacement", 0.0) < 0.14:
            feedback_items.append("Shake the G handshape slightly for green.")
    elif sign == "yellow":
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Use a clearer Y handshape with the thumb and pinky extended.")
        if metrics.get("horizontal_displacement", 0.0) < 0.14:
            feedback_items.append("Shake the Y handshape slightly for yellow.")
    elif sign == "white":
        if metrics.get("start_anchor_distance", 0.0) > 0.38:
            feedback_items.append("Start the white sign with your open hand closer to your chest.")
        if metrics.get("motion_score", 0.0) < 62.0:
            feedback_items.append("Pull the hand away from the chest while closing it more clearly.")
        if metrics.get("end_anchor_distance", 0.0) < metrics.get("start_anchor_distance", 0.0):
            feedback_items.append("Finish the sign farther from your chest than where it started.")
    elif sign == "happy":
        if metrics.get("start_anchor_distance", 0.0) > 0.38:
            feedback_items.append("Start the happy sign on your chest with a flat hand.")
        if metrics.get("motion_score", 0.0) < 62.0:
            feedback_items.append("Brush upward on the chest in clearer circular motions.")
        if metrics.get("hand_openness", 0.0) < 1.45:
            feedback_items.append("Keep the hand flatter instead of curling the fingers.")
    elif sign == "angry":
        if metrics.get("position_score", 0.0) < 58.0:
            feedback_items.append("Start the angry sign lower in front of your torso before pulling upward.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Pull both tense hands upward more sharply for angry.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Bend the fingers into clearer claw-like hands for angry.")
    elif sign == "tired":
        if metrics.get("start_anchor_distance", 0.0) > 0.36:
            feedback_items.append("Start the tired sign with both hands closer to your eyes.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Let both hands drop downward more clearly for tired.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Keep the index and middle fingers extended together for tired.")
    elif sign == "eat":
        if metrics.get("start_anchor_distance", 0.0) > 0.34:
            feedback_items.append("Bring the flat O hand closer to your mouth for eat.")
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Close the fingertips together into a clearer flat O handshape.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Tap the hand toward the mouth more clearly, like putting food in.")
    elif sign == "drink":
        if metrics.get("start_anchor_distance", 0.0) > 0.34:
            feedback_items.append("Start the C handshape closer to your mouth for drink.")
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Form a clearer C shape, like holding a cup.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Tilt the hand toward the mouth more clearly like drinking.")
    elif sign == "understand":
        if metrics.get("start_anchor_distance", 0.0) > 0.34:
            feedback_items.append("Start with the fist closer to your temple for understand.")
        if metrics.get("motion_score", 0.0) < 60.0:
            feedback_items.append("Flick the index finger up more clearly at the end of the sign.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Begin with a fist and let the index finger open up more clearly.")
    elif sign == "where":
        if metrics.get("start_anchor_distance", 0.0) > 0.36:
            feedback_items.append("Hold your index finger closer to the front of your face for where.")
        if metrics.get("horizontal_displacement", 0.0) < 0.16:
            feedback_items.append("Shake the index finger side to side more clearly for where.")
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Use a clearer pointing handshape with only the index finger extended.")
    elif sign == "who":
        if metrics.get("start_anchor_distance", 0.0) > 0.34:
            feedback_items.append("Bring the index finger closer to your lips for who.")
        if metrics.get("motion_score", 0.0) < 60.0:
            feedback_items.append("Circle the index finger around the lips more clearly.")
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Use a clearer pointing handshape with only the index finger extended.")
    elif sign == "water":
        if metrics.get("start_anchor_distance", 0.0) > 0.34:
            feedback_items.append("Bring the W handshape closer to your chin for water.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Tap the chin more clearly with the W handshape.")
        if metrics.get("shape_score", 0.0) < 62.0:
            feedback_items.append("Show a clearer W handshape with three fingers raised and the pinky tucked.")
    elif sign == "maybe":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Alternate the two flat hands up and down more clearly, like a scale.")
        if metrics.get("position_score", 0.0) < 58.0:
            feedback_items.append("Hold both hands out in front of you instead of stacking them too close together.")
    elif sign == "what":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Shake both open hands outward a little more clearly for what.")
        if metrics.get("hand_openness", 0.0) < 1.45:
            feedback_items.append("Keep the hands open with the palms up for what.")
    elif sign == "more":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Bring the two flat O hands together more clearly for more.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Close the fingertips together into clearer flat O handshapes.")
    elif sign == "finished":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Flip both open hands outward more clearly for finished.")
        if metrics.get("hand_openness", 0.0) < 1.75:
            feedback_items.append("Start with both hands more open before flipping them outward.")
    elif sign == "help":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Lift both hands upward together more clearly for help.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Place the thumb-up fist on the flat supporting palm more clearly.")
    elif sign == "stop":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Bring the flat hand down onto the other palm more sharply for stop.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Keep both hands flat so the top hand lands cleanly on the lower palm.")
    elif sign == "wait":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Tap the top two fingers onto the supporting palm more clearly for wait.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Keep the top hand in a clearer two-finger handshape for wait.")
        if metrics.get("position_score", 0.0) < 58.0:
            feedback_items.append("Hold the lower hand flat and steady under the tapping hand.")
    elif sign == "when":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Touch the index fingers and circle one around the other more clearly for when.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Keep both hands in clearer pointing handshapes for when.")
    elif sign == "how":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Rotate the bent hands outward and upward more clearly for how.")
        if metrics.get("shape_score", 0.0) < 60.0:
            feedback_items.append("Keep the hands bent with the knuckles touching before the rotation.")
    elif sign == "sad":
        if metrics.get("start_anchor_distance", 0.0) > 0.36:
            feedback_items.append("Start the sad sign higher in front of your face.")
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Move both open hands downward more clearly for sad.")
    elif sign == "love":
        if metrics.get("motion_score", 0.0) < 58.0:
            feedback_items.append("Cross both arms over your chest more clearly for love.")
        if metrics.get("position_score", 0.0) < 58.0:
            feedback_items.append("Finish with the hands tucked closer to the shoulders and chest.")

    if not feedback_items and not correct:
        weakest_area = min(
            (
                ("hand shape", comparison.get("shape_score", 0.0)),
                ("position", comparison.get("position_score", 0.0)),
                ("movement", comparison.get("motion_score", 0.0)),
            ),
            key=lambda item: item[1],
        )[0]
        feedback_items.append(f"Match the reference {weakest_area} more closely and try again.")

    feedback_items = feedback_items[:3]

    strong_parts = [
        part
        for part, value in (
            ("hand shape", comparison.get("shape_score", 0.0)),
            ("position", comparison.get("position_score", 0.0)),
            ("movement", comparison.get("motion_score", 0.0)),
        )
        if value >= 75.0
    ]

    if correct:
        if strong_parts:
            summary = f"Nice work. Your {label} sign scored {score:.0f}% and the {', '.join(strong_parts)} looked strong."
        else:
            summary = f"Nice work. Your {label} sign matched the reference pattern with a score of {score:.0f}%."
    else:
        if feedback_items:
            summary = f"Your {label} sign is close, but it still needs a few adjustments. Current score: {score:.0f}%."
        else:
            summary = f"Your {label} sign did not match the reference closely enough yet. Current score: {score:.0f}%."

    return summary, feedback_items
