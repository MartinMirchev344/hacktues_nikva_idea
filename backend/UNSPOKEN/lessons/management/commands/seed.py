from django.core.management.base import BaseCommand
from lessons.models import Lesson, Exercise


SEED_DATA = [
    {
        "title": "Greetings",
        "description": "Learn the most essential signs for meeting and greeting people.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 5,
        "exercises": [
            {
                "title": "Hello",
                "prompt": "Sign 'Hello'",
                "instructions": "Open your hand flat, fingers together. Touch your forehead with your fingertips, then wave your hand outward.",
                "expected_sign": "hello",
                "order": 1,
            },
            {
                "title": "Goodbye",
                "prompt": "Sign 'Goodbye'",
                "instructions": "Open your hand, fingers spread. Bend your fingers down and up repeatedly, like waving goodbye.",
                "expected_sign": "goodbye",
                "order": 2,
            },
            {
                "title": "Thank You",
                "prompt": "Sign 'Thank You'",
                "instructions": "Touch your chin or lips with the fingertips of your flat hand, then move your hand forward and down.",
                "expected_sign": "thank_you",
                "order": 3,
            },
            {
                "title": "Please",
                "prompt": "Sign 'Please'",
                "instructions": "Place your flat hand on your chest and move it in a circular motion.",
                "expected_sign": "please",
                "order": 4,
            },
            {
                "title": "Sorry",
                "prompt": "Sign 'Sorry'",
                "instructions": "Make a fist and rub it in a circular motion over your chest.",
                "expected_sign": "sorry",
                "order": 5,
            },
        ],
    },
    {
        "title": "Yes & No",
        "description": "Two of the most important words in any language.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 3,
        "exercises": [
            {
                "title": "Yes",
                "prompt": "Sign 'Yes'",
                "instructions": "Make a fist and bob it up and down, like a head nodding.",
                "expected_sign": "yes",
                "order": 1,
            },
            {
                "title": "No",
                "prompt": "Sign 'No'",
                "instructions": "Extend your index and middle fingers together with your thumb. Snap them together twice.",
                "expected_sign": "no",
                "order": 2,
            },
            {
                "title": "Maybe",
                "prompt": "Sign 'Maybe'",
                "instructions": "Hold both flat hands out, palms up. Alternate raising and lowering them like a scale.",
                "expected_sign": "maybe",
                "order": 3,
            },
        ],
    },
    {
        "title": "Numbers 1-5",
        "description": "Count from one to five in sign language.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 5,
        "exercises": [
            {
                "title": "One",
                "prompt": "Sign the number 1",
                "instructions": "Hold up your index finger with your palm facing outward.",
                "expected_sign": "one",
                "order": 1,
            },
            {
                "title": "Two",
                "prompt": "Sign the number 2",
                "instructions": "Hold up your index and middle fingers in a V shape.",
                "expected_sign": "two",
                "order": 2,
            },
            {
                "title": "Three",
                "prompt": "Sign the number 3",
                "instructions": "Hold up your thumb, index, and middle fingers.",
                "expected_sign": "three",
                "order": 3,
            },
            {
                "title": "Four",
                "prompt": "Sign the number 4",
                "instructions": "Hold up four fingers (all except thumb), spread apart.",
                "expected_sign": "four",
                "order": 4,
            },
            {
                "title": "Five",
                "prompt": "Sign the number 5",
                "instructions": "Hold up all five fingers, spread open.",
                "expected_sign": "five",
                "order": 5,
            },
        ],
    },
    {
        "title": "Numbers 6-10",
        "description": "Continue counting from six to ten.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 5,
        "exercises": [
            {
                "title": "Six",
                "prompt": "Sign the number 6",
                "instructions": "Touch your pinky finger to your thumb, other fingers extended.",
                "expected_sign": "six",
                "order": 1,
            },
            {
                "title": "Seven",
                "prompt": "Sign the number 7",
                "instructions": "Touch your ring finger to your thumb, other fingers extended.",
                "expected_sign": "seven",
                "order": 2,
            },
            {
                "title": "Eight",
                "prompt": "Sign the number 8",
                "instructions": "Touch your middle finger to your thumb, other fingers extended.",
                "expected_sign": "eight",
                "order": 3,
            },
            {
                "title": "Nine",
                "prompt": "Sign the number 9",
                "instructions": "Touch your index finger to your thumb, other fingers extended.",
                "expected_sign": "nine",
                "order": 4,
            },
            {
                "title": "Ten",
                "prompt": "Sign the number 10",
                "instructions": "Hold up your thumb and shake your hand slightly from side to side.",
                "expected_sign": "ten",
                "order": 5,
            },
        ],
    },
    {
        "title": "Family",
        "description": "Signs for the people closest to you.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 7,
        "exercises": [
            {
                "title": "Mother",
                "prompt": "Sign 'Mother'",
                "instructions": "Spread your fingers apart and tap your chin twice with your thumb.",
                "expected_sign": "mother",
                "order": 1,
            },
            {
                "title": "Father",
                "prompt": "Sign 'Father'",
                "instructions": "Spread your fingers apart and tap your forehead twice with your thumb.",
                "expected_sign": "father",
                "order": 2,
            },
            {
                "title": "Brother",
                "prompt": "Sign 'Brother'",
                "instructions": "Point your index fingers together at chin level, then bring both hands down pointing forward.",
                "expected_sign": "brother",
                "order": 3,
            },
            {
                "title": "Sister",
                "prompt": "Sign 'Sister'",
                "instructions": "Point your index fingers together at jaw level, then bring both hands down pointing forward.",
                "expected_sign": "sister",
                "order": 4,
            },
            {
                "title": "Friend",
                "prompt": "Sign 'Friend'",
                "instructions": "Hook your right index finger over your left index finger, then reverse.",
                "expected_sign": "friend",
                "order": 5,
            },
        ],
    },
    {
        "title": "Colors",
        "description": "Learn the signs for basic colors.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 7,
        "exercises": [
            {
                "title": "Red",
                "prompt": "Sign 'Red'",
                "instructions": "Point your index finger to your lips and brush it downward.",
                "expected_sign": "red",
                "order": 1,
            },
            {
                "title": "Blue",
                "prompt": "Sign 'Blue'",
                "instructions": "Hold the letter B handshape and shake it slightly.",
                "expected_sign": "blue",
                "order": 2,
            },
            {
                "title": "Green",
                "prompt": "Sign 'Green'",
                "instructions": "Hold the letter G handshape and shake it slightly.",
                "expected_sign": "green",
                "order": 3,
            },
            {
                "title": "Yellow",
                "prompt": "Sign 'Yellow'",
                "instructions": "Hold the letter Y handshape and shake it slightly.",
                "expected_sign": "yellow",
                "order": 4,
            },
            {
                "title": "White",
                "prompt": "Sign 'White'",
                "instructions": "Place your open hand on your chest, fingers spread, then pull it away closing into a flat O shape.",
                "expected_sign": "white",
                "order": 5,
            },
            {
                "title": "Black",
                "prompt": "Sign 'Black'",
                "instructions": "Slide your index finger across your forehead from left to right.",
                "expected_sign": "black",
                "order": 6,
            },
        ],
    },
    {
        "title": "Feelings",
        "description": "Express how you feel.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 7,
        "exercises": [
            {
                "title": "Happy",
                "prompt": "Sign 'Happy'",
                "instructions": "Brush your flat hand upward on your chest in circular motions twice.",
                "expected_sign": "happy",
                "order": 1,
            },
            {
                "title": "Sad",
                "prompt": "Sign 'Sad'",
                "instructions": "Hold both open hands in front of your face and move them downward.",
                "expected_sign": "sad",
                "order": 2,
            },
            {
                "title": "Angry",
                "prompt": "Sign 'Angry'",
                "instructions": "Place your bent fingers on your chin and move your hand forward while bending into a claw.",
                "expected_sign": "angry",
                "order": 3,
            },
            {
                "title": "Tired",
                "prompt": "Sign 'Tired'",
                "instructions": "Place bent hands on your chest with fingertips touching, then rotate them downward.",
                "expected_sign": "tired",
                "order": 4,
            },
            {
                "title": "Love",
                "prompt": "Sign 'Love'",
                "instructions": "Cross your arms over your chest, like hugging yourself.",
                "expected_sign": "love",
                "order": 5,
            },
        ],
    },
    {
        "title": "Common Questions",
        "description": "Ask the most useful everyday questions.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 8,
        "exercises": [
            {
                "title": "What",
                "prompt": "Sign 'What'",
                "instructions": "Hold your hands out, palms up, and shake them slightly side to side with a questioning expression.",
                "expected_sign": "what",
                "order": 1,
            },
            {
                "title": "Where",
                "prompt": "Sign 'Where'",
                "instructions": "Hold up your index finger and shake it side to side.",
                "expected_sign": "where",
                "order": 2,
            },
            {
                "title": "Who",
                "prompt": "Sign 'Who'",
                "instructions": "Circle your index finger around your lips.",
                "expected_sign": "who",
                "order": 3,
            },
            {
                "title": "When",
                "prompt": "Sign 'When'",
                "instructions": "Hold up your index finger on both hands, touch the tips together, then circle one around the other.",
                "expected_sign": "when",
                "order": 4,
            },
            {
                "title": "How",
                "prompt": "Sign 'How'",
                "instructions": "Place bent hands together, knuckles touching, then rotate them outward and upward.",
                "expected_sign": "how",
                "order": 5,
            },
        ],
    },
    {
        "title": "Food & Drink",
        "description": "Signs you need at the table.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 8,
        "exercises": [
            {
                "title": "Eat",
                "prompt": "Sign 'Eat'",
                "instructions": "Bring your flat O hand to your mouth, as if putting food in.",
                "expected_sign": "eat",
                "order": 1,
            },
            {
                "title": "Drink",
                "prompt": "Sign 'Drink'",
                "instructions": "Form a C shape with your hand and tilt it toward your mouth like drinking from a cup.",
                "expected_sign": "drink",
                "order": 2,
            },
            {
                "title": "Water",
                "prompt": "Sign 'Water'",
                "instructions": "Hold up the letter W and tap your chin twice with your index finger.",
                "expected_sign": "water",
                "order": 3,
            },
            {
                "title": "More",
                "prompt": "Sign 'More'",
                "instructions": "Bring both flat O hands together, fingertips touching, repeatedly.",
                "expected_sign": "more",
                "order": 4,
            },
            {
                "title": "Finished",
                "prompt": "Sign 'Finished'",
                "instructions": "Hold both open hands up, palms facing you, then quickly flip them outward.",
                "expected_sign": "finished",
                "order": 5,
            },
        ],
    },
    {
        "title": "Asking for Help",
        "description": "Signs for when you need assistance.",
        "difficulty": "beginner",
        "estimated_duration_minutes": 5,
        "exercises": [
            {
                "title": "Help",
                "prompt": "Sign 'Help'",
                "instructions": "Place your closed fist (thumb up) on your flat palm and lift both hands upward together.",
                "expected_sign": "help",
                "order": 1,
            },
            {
                "title": "Stop",
                "prompt": "Sign 'Stop'",
                "instructions": "Bring your flat hand down sharply onto your other flat palm.",
                "expected_sign": "stop",
                "order": 2,
            },
            {
                "title": "Wait",
                "prompt": "Sign 'Wait'",
                "instructions": "Hold both hands out with fingers spread, wiggling them slightly.",
                "expected_sign": "wait",
                "order": 3,
            },
            {
                "title": "Understand",
                "prompt": "Sign 'Understand'",
                "instructions": "Hold a fist near your temple, then flick your index finger up.",
                "expected_sign": "understand",
                "order": 4,
            },
        ],
    },
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

        for lesson_data in SEED_DATA:
            exercises_data = lesson_data.pop("exercises")
            lesson, created = Lesson.objects.get_or_create(
                title=lesson_data["title"],
                defaults={**lesson_data, "sign_language": "ASL", "is_published": True},
            )
            if created:
                created_lessons += 1

            for ex in exercises_data:
                _, ex_created = Exercise.objects.get_or_create(
                    lesson=lesson,
                    order=ex["order"],
                    defaults={**ex, "exercise_type": "gesture_practice", "passing_score": 70},
                )
                if ex_created:
                    created_exercises += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created_lessons} lessons and {created_exercises} exercises."
        ))
