# seeds.py

from src.app import create_app
from src.model import db, Exercise

# Create the Flask app using the factory
app = create_app()

# Define your seed data and insertion logic
def seed_exercises():
    default_exercises = [
        {
            "name": "Push-Up",
            "description": "Start in a plank, lower chest to floor, then press back up.",
            "category": "strength",
            "muscle_group": "chest",
        },
        {
            "name": "Squat",
            "description": "Stand feet shoulder-width, bend knees and hips to lower down, then stand up.",
            "category": "strength",
            "muscle_group": "legs",
        },
        {
            "name": "Jumping Jack",
            "description": "Jump feet out while lifting arms overhead, then return.",
            "category": "cardio",
            "muscle_group": "full body",
        },
        {
            "name": "Plank",
            "description": "Hold a straight-body position on elbows and toes.",
            "category": "flexibility",
            "muscle_group": "core",
        },
        # …add more exercises as needed…
    ]

    inserted = 0
    for data in default_exercises:
        # only insert if the exercise doesn't already exist
        if not Exercise.query.filter_by(name=data["name"]).first():
            ex = Exercise(**data)
            db.session.add(ex)
            inserted += 1

    db.session.commit()
    print(f"✅ Seeded {inserted} new exercises (of {len(default_exercises)} total).")

# Run the seeder within the Flask app context
if __name__ == "__main__":
    with app.app_context():
        seed_exercises()
