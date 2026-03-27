from django.core.management.base import BaseCommand
from lessons.models import Lesson, Exercise


MOTION_PATTERNS = (
    "outward_wave",
    "finger_wave",
    "forward_release",
    "circle",
    "fist_circle",
)


def build_quiz_preview(instructions, index):
    return {
        "motion": MOTION_PATTERNS[(index - 1) % len(MOTION_PATTERNS)],
        "cue": instructions,
        "steps": [
            "Watch where the sign begins.",
            "Follow the main hand movement.",
            "Type the word or phrase you think is being signed.",
        ],
    }


def build_exercises(vocabulary, quiz_prompt, quiz_instructions):
    exercises = []

    for index, item in enumerate(vocabulary, start=1):
        practice_order = (index * 2) - 1
        quiz_order = practice_order + 1

        exercises.append(
            {
                "title": f"{item['title']} Practice",
                "prompt": item["prompt"],
                "instructions": item["instructions"],
                "expected_sign": item["expected_sign"],
                "order": practice_order,
                "exercise_type": "gesture_practice",
            }
        )
        exercises.append(
            {
                "title": f"Sign Check {index}",
                "prompt": quiz_prompt,
                "instructions": quiz_instructions,
                "expected_sign": item["expected_sign"],
                "order": quiz_order,
                "exercise_type": "quiz",
                "target_motion_data": build_quiz_preview(
                    item["instructions"],
                    index,
                ),
            }
        )

    return exercises


def build_lesson(
    title,
    description,
    difficulty,
    estimated_duration_minutes,
    vocabulary,
    quiz_prompt,
    quiz_instructions,
):
    return {
        "title": title,
        "description": description,
        "difficulty": difficulty,
        "estimated_duration_minutes": estimated_duration_minutes * 2,
        "exercises": build_exercises(
            vocabulary,
            quiz_prompt,
            quiz_instructions,
        ),
    }


SEED_DATA = [
    build_lesson(
        "Greetings",
        "Learn the most essential signs for meeting and greeting people.",
        "beginner",
        5,
        [
            {
                "title": "Hello",
                "prompt": "Sign 'Hello'",
                "instructions": "Open your hand flat, fingers together. Touch your forehead with your fingertips, then wave your hand outward.",
                "expected_sign": "hello",
            },
            {
                "title": "Goodbye",
                "prompt": "Sign 'Goodbye'",
                "instructions": "Open your hand, fingers spread. Bend your fingers down and up repeatedly, like waving goodbye.",
                "expected_sign": "goodbye",
            },
            {
                "title": "Thank You",
                "prompt": "Sign 'Thank You'",
                "instructions": "Touch your chin or lips with the fingertips of your flat hand, then move your hand forward and down.",
                "expected_sign": "thank_you",
            },
            {
                "title": "Please",
                "prompt": "Sign 'Please'",
                "instructions": "Place your flat hand on your chest and move it in a circular motion.",
                "expected_sign": "please",
            },
            {
                "title": "Sorry",
                "prompt": "Sign 'Sorry'",
                "instructions": "Make a fist and rub it in a circular motion over your chest.",
                "expected_sign": "sorry",
            },
        ],
        "Watch the sign and guess the greeting",
        "Watch the looping sign demo and type the greeting word or phrase being signed.",
    ),
    build_lesson(
        "Yes & No",
        "Two of the most important words in any language.",
        "beginner",
        3,
        [
            {
                "title": "Yes",
                "prompt": "Sign 'Yes'",
                "instructions": "Make a fist and bob it up and down, like a head nodding.",
                "expected_sign": "yes",
            },
            {
                "title": "No",
                "prompt": "Sign 'No'",
                "instructions": "Extend your index and middle fingers together with your thumb. Snap them together twice.",
                "expected_sign": "no",
            },
            {
                "title": "Maybe",
                "prompt": "Sign 'Maybe'",
                "instructions": "Hold both flat hands out, palms up. Alternate raising and lowering them like a scale.",
                "expected_sign": "maybe",
            },
        ],
        "Watch the sign and guess the answer",
        "Watch the looping sign demo and type the word being signed.",
    ),
    build_lesson(
        "Numbers 1-5",
        "Count from one to five in sign language.",
        "beginner",
        5,
        [
            {
                "title": "One",
                "prompt": "Sign the number 1",
                "instructions": "Hold up your index finger with your palm facing outward.",
                "expected_sign": "one",
            },
            {
                "title": "Two",
                "prompt": "Sign the number 2",
                "instructions": "Hold up your index and middle fingers in a V shape.",
                "expected_sign": "two",
            },
            {
                "title": "Three",
                "prompt": "Sign the number 3",
                "instructions": "Hold up your thumb, index, and middle fingers.",
                "expected_sign": "three",
            },
            {
                "title": "Four",
                "prompt": "Sign the number 4",
                "instructions": "Hold up four fingers (all except thumb), spread apart.",
                "expected_sign": "four",
            },
            {
                "title": "Five",
                "prompt": "Sign the number 5",
                "instructions": "Hold up all five fingers, spread open.",
                "expected_sign": "five",
            },
        ],
        "Watch the sign and guess the number",
        "Watch the looping sign demo and type the number word being signed.",
    ),
    build_lesson(
        "Numbers 6-10",
        "Continue counting from six to ten.",
        "beginner",
        5,
        [
            {
                "title": "Six",
                "prompt": "Sign the number 6",
                "instructions": "Touch your pinky finger to your thumb, other fingers extended.",
                "expected_sign": "six",
            },
            {
                "title": "Seven",
                "prompt": "Sign the number 7",
                "instructions": "Touch your ring finger to your thumb, other fingers extended.",
                "expected_sign": "seven",
            },
            {
                "title": "Eight",
                "prompt": "Sign the number 8",
                "instructions": "Touch your middle finger to your thumb, other fingers extended.",
                "expected_sign": "eight",
            },
            {
                "title": "Nine",
                "prompt": "Sign the number 9",
                "instructions": "Touch your index finger to your thumb, other fingers extended.",
                "expected_sign": "nine",
            },
            {
                "title": "Ten",
                "prompt": "Sign the number 10",
                "instructions": "Hold up your thumb and shake your hand slightly from side to side.",
                "expected_sign": "ten",
            },
        ],
        "Watch the sign and guess the number",
        "Watch the looping sign demo and type the number word being signed.",
    ),
    build_lesson(
        "Family",
        "Signs for the people closest to you.",
        "beginner",
        7,
        [
            {
                "title": "Mother",
                "prompt": "Sign 'Mother'",
                "instructions": "Spread your fingers apart and tap your chin twice with your thumb.",
                "expected_sign": "mother",
            },
            {
                "title": "Father",
                "prompt": "Sign 'Father'",
                "instructions": "Spread your fingers apart and tap your forehead twice with your thumb.",
                "expected_sign": "father",
            },
            {
                "title": "Brother",
                "prompt": "Sign 'Brother'",
                "instructions": "Dominant hand forms an L-shape and touches the side of your forehead, then both hands come together with index fingers pointing forward.",
                "expected_sign": "brother",
            },
            {
                "title": "Sister",
                "prompt": "Sign 'Sister'",
                "instructions": "Dominant hand forms an L-shape and touches the side of your chin, then both hands come together with index fingers pointing forward.",
                "expected_sign": "sister",
            },
            {
                "title": "Friend",
                "prompt": "Sign 'Friend'",
                "instructions": "Hook your right index finger over your left index finger, then reverse.",
                "expected_sign": "friend",
            },
        ],
        "Watch the sign and guess the family word",
        "Watch the looping sign demo and type the family word being signed.",
    ),
    build_lesson(
        "Colors",
        "Learn the signs for basic colors.",
        "beginner",
        7,
        [
            {
                "title": "Red",
                "prompt": "Sign 'Red'",
                "instructions": "Point your index finger to your lips and brush it downward.",
                "expected_sign": "red",
            },
            {
                "title": "Blue",
                "prompt": "Sign 'Blue'",
                "instructions": "Hold the letter B handshape and shake it slightly.",
                "expected_sign": "blue",
            },
            {
                "title": "Green",
                "prompt": "Sign 'Green'",
                "instructions": "Hold the letter G handshape and shake it slightly.",
                "expected_sign": "green",
            },
            {
                "title": "Yellow",
                "prompt": "Sign 'Yellow'",
                "instructions": "Hold the letter Y handshape and shake it slightly.",
                "expected_sign": "yellow",
            },
            {
                "title": "White",
                "prompt": "Sign 'White'",
                "instructions": "Place your open hand on your chest, fingers spread, then pull it away closing into a flat O shape.",
                "expected_sign": "white",
            },
            {
                "title": "Black",
                "prompt": "Sign 'Black'",
                "instructions": "Slide your index finger across your forehead from left to right.",
                "expected_sign": "black",
            },
        ],
        "Watch the sign and guess the color",
        "Watch the looping sign demo and type the color being signed.",
    ),
    build_lesson(
        "Feelings",
        "Express how you feel.",
        "beginner",
        7,
        [
            {
                "title": "Happy",
                "prompt": "Sign 'Happy'",
                "instructions": "Brush your flat hand upward on your chest in circular motions twice.",
                "expected_sign": "happy",
            },
            {
                "title": "Sad",
                "prompt": "Sign 'Sad'",
                "instructions": "Hold both open hands in front of your face and move them downward.",
                "expected_sign": "sad",
            },
            {
                "title": "Angry",
                "prompt": "Sign 'Angry'",
                "instructions": "Hold both hands in front of your chest with fingers curved like claws, then pull them upward and outward forcefully.",
                "expected_sign": "angry",
            },
            {
                "title": "Tired",
                "prompt": "Sign 'Tired'",
                "instructions": "Place bent hands on your chest with fingertips touching, then rotate them downward.",
                "expected_sign": "tired",
            },
            {
                "title": "Love",
                "prompt": "Sign 'Love'",
                "instructions": "Cross your arms over your chest, like hugging yourself.",
                "expected_sign": "love",
            },
        ],
        "Watch the sign and guess the feeling",
        "Watch the looping sign demo and type the feeling word being signed.",
    ),
    build_lesson(
        "Common Questions",
        "Ask the most useful everyday questions.",
        "beginner",
        8,
        [
            {
                "title": "What",
                "prompt": "Sign 'What'",
                "instructions": "Hold your hands out, palms up, and shake them slightly side to side with a questioning expression.",
                "expected_sign": "what",
            },
            {
                "title": "Where",
                "prompt": "Sign 'Where'",
                "instructions": "Hold up your index finger and shake it side to side.",
                "expected_sign": "where",
            },
            {
                "title": "Who",
                "prompt": "Sign 'Who'",
                "instructions": "Circle your index finger around your lips.",
                "expected_sign": "who",
            },
            {
                "title": "When",
                "prompt": "Sign 'When'",
                "instructions": "Hold up your index finger on both hands, touch the tips together, then circle one around the other.",
                "expected_sign": "when",
            },
            {
                "title": "How",
                "prompt": "Sign 'How'",
                "instructions": "Place bent hands together, knuckles touching, then rotate them outward and upward.",
                "expected_sign": "how",
            },
        ],
        "Watch the sign and guess the question word",
        "Watch the looping sign demo and type the question word being signed.",
    ),
    build_lesson(
        "Food & Drink",
        "Signs you need at the table.",
        "beginner",
        8,
        [
            {
                "title": "Eat",
                "prompt": "Sign 'Eat'",
                "instructions": "Bring your flat O hand to your mouth, as if putting food in.",
                "expected_sign": "eat",
            },
            {
                "title": "Drink",
                "prompt": "Sign 'Drink'",
                "instructions": "Form a C shape with your hand and tilt it toward your mouth like drinking from a cup.",
                "expected_sign": "drink",
            },
            {
                "title": "Water",
                "prompt": "Sign 'Water'",
                "instructions": "Hold up the letter W and tap your chin twice with your index finger.",
                "expected_sign": "water",
            },
            {
                "title": "More",
                "prompt": "Sign 'More'",
                "instructions": "Bring both flat O hands together, fingertips touching, repeatedly.",
                "expected_sign": "more",
            },
            {
                "title": "Finished",
                "prompt": "Sign 'Finished'",
                "instructions": "Hold both open hands up, palms facing you, then quickly flip them outward.",
                "expected_sign": "finished",
            },
        ],
        "Watch the sign and guess the food phrase",
        "Watch the looping sign demo and type the food or drink word being signed.",
    ),
    build_lesson(
        "Asking for Help",
        "Signs for when you need assistance.",
        "beginner",
        5,
        [
            {
                "title": "Help",
                "prompt": "Sign 'Help'",
                "instructions": "Place your closed fist (thumb up) on your flat palm and lift both hands upward together.",
                "expected_sign": "help",
            },
            {
                "title": "Stop",
                "prompt": "Sign 'Stop'",
                "instructions": "Bring your flat hand down sharply onto your other flat palm.",
                "expected_sign": "stop",
            },
            {
                "title": "Wait",
                "prompt": "Sign 'Wait'",
                "instructions": "Hold both hands out with fingers spread, wiggling them slightly.",
                "expected_sign": "wait",
            },
            {
                "title": "Understand",
                "prompt": "Sign 'Understand'",
                "instructions": "Hold a fist near your temple, then flick your index finger up.",
                "expected_sign": "understand",
            },
        ],
        "Watch the sign and guess the help word",
        "Watch the looping sign demo and type the word or phrase being signed.",
    ),
]


class Command(BaseCommand):
    help = "Seed the database with beginner ASL lessons and exercises"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing lessons before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Lesson.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all existing lessons."))

        created_lessons = 0
        created_exercises = 0
        updated_lessons = 0
        updated_exercises = 0
        deleted_exercises = 0

        for lesson_data in SEED_DATA:
            exercises_data = lesson_data["exercises"]
            lesson_fields = {
                **{k: v for k, v in lesson_data.items() if k != "exercises"},
                "sign_language": "ASL",
                "is_published": True,
            }
            lesson, created = Lesson.objects.update_or_create(
                title=lesson_data["title"],
                defaults=lesson_fields,
            )
            if created:
                created_lessons += 1
            else:
                updated_lessons += 1

            seeded_orders = []

            for ex in exercises_data:
                seeded_orders.append(ex["order"])
                _, ex_created = Exercise.objects.update_or_create(
                    lesson=lesson,
                    order=ex["order"],
                    defaults={
                        **ex,
                        "exercise_type": ex.get("exercise_type", "gesture_practice"),
                        "passing_score": ex.get("passing_score", 70),
                        "repetitions_target": ex.get("repetitions_target", 1),
                        "target_pose_data": ex.get("target_pose_data", {}),
                        "target_motion_data": ex.get("target_motion_data", {}),
                    },
                )
                if ex_created:
                    created_exercises += 1
                else:
                    updated_exercises += 1

            deleted_exercises += Exercise.objects.filter(lesson=lesson).exclude(order__in=seeded_orders).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            "Done. "
            f"Created {created_lessons} lessons, updated {updated_lessons} lessons, "
            f"created {created_exercises} exercises, updated {updated_exercises} exercises, "
            f"deleted {deleted_exercises} stale exercises."
        ))
