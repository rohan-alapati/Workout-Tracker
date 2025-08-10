# src/workouts.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from src.model import db, Workout, WorkoutExercise, ScheduledWorkout

workouts_bp = Blueprint("workouts", __name__, url_prefix="/workouts")


# Helper: serialize a Workout (including its exercises)
def serialize_workout(w):
    return {
        "id": w.id,
        "title": w.title,
        "notes": w.notes,
        "created_at": w.created_at.isoformat(),
        "exercises": [
            {
                "id": we.id,
                "exercise_id": we.exercise_id,
                "exercise_name": we.exercise.name,
                "sets": we.sets,
                "reps": we.reps,
                "weight": we.weight,
            }
            for we in w.exercises
        ],
    }


@workouts_bp.route("", methods=["POST"])
@jwt_required()
def create_workout():
    """
    Create workout
    ---
    tags: [Workouts]
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: workout
        required: true
        schema:
          type: object
          required: [title, exercises]
          properties:
            title: {type: string, example: "Leg Day"}
            notes: {type: string, example: "Felt strong"}
            exercises:
              type: array
              items:
                type: object
                required: [exercise_id, sets, reps]
                properties:
                  exercise_id: {type: integer, example: 1}
                  sets:        {type: integer, example: 4}
                  reps:        {type: integer, example: 10}
                  weight:      {type: number,  example: 135}
    responses:
      201:
        description: Created
        schema:
          type: object
          properties:
            id:    {type: integer}
            title: {type: string}
            notes: {type: string}
            exercises:
              type: array
              items:
                type: object
                properties:
                  id:           {type: integer}
                  exercise_id:  {type: integer}
                  exercise_name:{type: string}
                  sets:         {type: integer}
                  reps:         {type: integer}
                  weight:       {type: number}
      400:
        description: Validation error
    """
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    title = data.get("title")
    exercises = data.get("exercises", [])  # list of {exercise_id, sets, reps, weight}
    if not title or not exercises:
        return jsonify(msg="title and exercises required"), 400

    # Create workout
    w = Workout(user_id=user_id, title=title, notes=data.get("notes"))
    db.session.add(w)
    db.session.flush()  # get w.id

    # Link exercises
    for ex in exercises:
        # Optionally validate ex['exercise_id'] exists
        we = WorkoutExercise(
            workout_id=w.id,
            exercise_id=ex["exercise_id"],
            sets=ex["sets"],
            reps=ex["reps"],
            weight=ex.get("weight", 0),
        )
        db.session.add(we)

    db.session.commit()
    return jsonify(serialize_workout(w)), 201


@workouts_bp.route("", methods=["GET"])
@jwt_required()
def list_workouts():
    user_id = get_jwt_identity()
    ws = Workout.query.filter_by(user_id=user_id).order_by(Workout.created_at.desc())
    return jsonify([serialize_workout(w) for w in ws])


@workouts_bp.route("/<int:wid>", methods=["GET"])
@jwt_required()
def get_workout(wid):
    user_id = get_jwt_identity()
    w = Workout.query.filter_by(id=wid, user_id=user_id).first_or_404()
    return jsonify(serialize_workout(w))


@workouts_bp.route("/<int:wid>", methods=["PUT"])
@jwt_required()
def update_workout(wid):
    user_id = get_jwt_identity()
    w = Workout.query.filter_by(id=wid, user_id=user_id).first_or_404()
    data = request.get_json() or {}
    w.title = data.get("title", w.title)
    w.notes = data.get("notes", w.notes)

    # Optional: clear & re-add exercises
    if "exercises" in data:
        WorkoutExercise.query.filter_by(workout_id=w.id).delete()
        for ex in data["exercises"]:
            we = WorkoutExercise(
                workout_id=w.id,
                exercise_id=ex["exercise_id"],
                sets=ex["sets"],
                reps=ex["reps"],
                weight=ex.get("weight", 0),
            )
            db.session.add(we)

    db.session.commit()
    return jsonify(serialize_workout(w))


@workouts_bp.route("/<int:wid>", methods=["DELETE"])
@jwt_required()
def delete_workout(wid):
    user_id = get_jwt_identity()
    w = Workout.query.filter_by(id=wid, user_id=user_id).first_or_404()
    db.session.delete(w)
    db.session.commit()
    return jsonify(msg="deleted"), 200


@workouts_bp.route("/<int:wid>/schedule", methods=["POST"])
@jwt_required()
def schedule_workout(wid):
    user_id = int(get_jwt_identity())
    w = Workout.query.filter_by(id=wid, user_id=user_id).first_or_404()

    data = request.get_json() or {}
    dt_str = data.get("scheduled_at")
    if not dt_str:
        return jsonify(msg="scheduled_at (ISO datetime) required"), 400

    # parse & validate
    try:
        scheduled = datetime.fromisoformat(dt_str)
    except ValueError:
        return jsonify(msg="invalid datetime format"), 400

    sw = ScheduledWorkout(workout_id=w.id, scheduled_at=scheduled)
    db.session.add(sw)
    db.session.commit()
    return jsonify(id=sw.id, scheduled_at=sw.scheduled_at.isoformat()), 201


@workouts_bp.route("/<int:wid>/schedule", methods=["GET"])
@jwt_required()
def list_workout_schedules(wid):
    user_id = int(get_jwt_identity())
    w = Workout.query.filter_by(id=wid, user_id=user_id).first_or_404()

    return jsonify(
        [
            {"id": s.id, "scheduled_at": s.scheduled_at.isoformat()}
            for s in w.scheduled_workouts
        ]
    )


@workouts_bp.route("/<int:wid>/schedule/<int:sid>", methods=["PUT"])
@jwt_required()
def reschedule_workout(wid, sid):
    user_id = int(get_jwt_identity())
    s = (
        ScheduledWorkout.query.join(Workout)
        .filter(
            Workout.user_id == user_id,
            ScheduledWorkout.id == sid,
            ScheduledWorkout.workout_id == wid,
        )
        .first_or_404()
    )

    data = request.get_json() or {}
    when = data.get("scheduled_at")
    if not when:
        return jsonify(msg="scheduled_at (ISO datetime) required"), 400
    try:
        s.scheduled_at = datetime.fromisoformat(when)
    except ValueError:
        return jsonify(msg="invalid datetime format"), 400

    db.session.commit()
    return jsonify(id=s.id, scheduled_at=s.scheduled_at.isoformat())


@workouts_bp.route("/<int:wid>/schedule/<int:sid>", methods=["DELETE"])
@jwt_required()
def cancel_workout_schedule(wid, sid):
    user_id = int(get_jwt_identity())
    s = (
        ScheduledWorkout.query.join(Workout)
        .filter(
            Workout.user_id == user_id,
            ScheduledWorkout.id == sid,
            ScheduledWorkout.workout_id == wid,
        )
        .first_or_404()
    )
    db.session.delete(s)
    db.session.commit()
    return jsonify(msg="schedule canceled"), 200
