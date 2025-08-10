from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta
from src.model import db, Workout, WorkoutExercise, Exercise, ScheduledWorkout

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


# Helper: window parser
def _parse_window_days(default=30):
    try:
        days = int(request.args.get("days", default))
        return max(1, min(days, 365))
    except ValueError:
        return default


@reports_bp.route("/overview", methods=["GET"])
@jwt_required()
def overview():
    user_id = int(get_jwt_identity())

    # total workouts
    total = (
        db.session.query(func.count(Workout.id))
        .filter(Workout.user_id == user_id)
        .scalar()
    )

    # total sets/reps/volume across all time
    agg = (
        db.session.query(
            func.coalesce(func.sum(WorkoutExercise.sets), 0),
            func.coalesce(func.sum(WorkoutExercise.reps), 0),
            func.coalesce(
                func.sum(
                    WorkoutExercise.sets
                    * WorkoutExercise.reps
                    * func.coalesce(WorkoutExercise.weight, 0)
                ),
                0.0,
            ),
        )
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .filter(Workout.user_id == user_id)
        .one()
    )
    total_sets, total_reps, total_volume = agg

    # top weight by exercise
    top_by_ex = (
        db.session.query(
            Exercise.name, func.coalesce(func.max(WorkoutExercise.weight), 0.0)
        )
        .join(WorkoutExercise, Exercise.id == WorkoutExercise.exercise_id)
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .filter(Workout.user_id == user_id)
        .group_by(Exercise.name)
        .order_by(Exercise.name)
        .all()
    )

    return jsonify(
        {
            "totals": {
                "workouts": total,
                "sets": int(total_sets or 0),
                "reps": int(total_reps or 0),
                "volume": float(total_volume or 0.0),
            },
            "top_weight_by_exercise": [
                {"exercise": name, "max_weight": float(m)} for (name, m) in top_by_ex
            ],
        }
    )


@reports_bp.route("/weekly", methods=["GET"])
@jwt_required()
def weekly():
    """Workouts per week for the last N weeks (default 8)."""
    user_id = int(get_jwt_identity())
    weeks = int(request.args.get("weeks", 8))
    weeks = max(1, min(weeks, 52))

    # SQLite-friendly week key
    week_rows = (
        db.session.query(
            func.strftime("%Y-%W", Workout.created_at).label("week"),
            func.count(Workout.id).label("count"),
        )
        .filter(Workout.user_id == user_id)
        .group_by("week")
        .order_by("week")
        .all()
    )

    return jsonify([{"week": w, "count": c} for (w, c) in week_rows][-weeks:])


@reports_bp.route("/exercise/<int:exercise_id>/progress", methods=["GET"])
@jwt_required()
def exercise_progress(exercise_id):
    """Time series of best weight and total volume per day for one exercise over a window."""
    user_id = int(get_jwt_identity())
    days = _parse_window_days(30)
    since = datetime.utcnow() - timedelta(days=days)

    # per-day best weight & volume (sets*reps*weight)
    rows = (
        db.session.query(
            func.strftime("%Y-%m-%d", Workout.created_at).label("day"),
            func.coalesce(func.max(WorkoutExercise.weight), 0.0).label("best_weight"),
            func.coalesce(
                func.sum(
                    WorkoutExercise.sets
                    * WorkoutExercise.reps
                    * func.coalesce(WorkoutExercise.weight, 0)
                ),
                0.0,
            ).label("volume"),
        )
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .filter(
            Workout.user_id == user_id,
            WorkoutExercise.exercise_id == exercise_id,
            Workout.created_at >= since,
        )
        .group_by("day")
        .order_by("day")
        .all()
    )

    # exercise name (if exists)
    ex = Exercise.query.get(exercise_id)
    return jsonify(
        {
            "exercise_id": exercise_id,
            "exercise_name": ex.name if ex else None,
            "window_days": days,
            "series": [
                {"day": d, "best_weight": float(bw), "volume": float(v)}
                for (d, bw, v) in rows
            ],
        }
    )


@reports_bp.route("/upcoming", methods=["GET"])
@jwt_required()
def upcoming():
    """Upcoming scheduled workouts sorted by time."""
    user_id = int(get_jwt_identity())
    rows = (
        db.session.query(
            ScheduledWorkout.id,
            ScheduledWorkout.workout_id,
            ScheduledWorkout.scheduled_at,
            Workout.title,
        )
        .join(Workout, Workout.id == ScheduledWorkout.workout_id)
        .filter(
            Workout.user_id == user_id,
            ScheduledWorkout.scheduled_at >= datetime.utcnow(),
        )
        .order_by(ScheduledWorkout.scheduled_at.asc())
        .all()
    )
    return jsonify(
        [
            {
                "id": sid,
                "workout_id": wid,
                "title": title,
                "scheduled_at": dt.isoformat(),
            }
            for (sid, wid, dt, title) in rows
        ]
    )
