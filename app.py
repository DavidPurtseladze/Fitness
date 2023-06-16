from flask import Flask, jsonify
from flask import request, render_template
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
db = SQLAlchemy(app)
#


class Exercise(db.Model):
    __tablename__ = 'exercise'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rep = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    distance = db.Column(db.Float, nullable=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rep': self.rep,
            'weight': self.weight,
            'duration': self.duration,
            'distance': self.distance,
            'workout_id': self.workout_id
        }

class Workout(db.Model):
    __tablename__ = 'workout'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    exercises = db.relationship('Exercise', backref='workout', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'duration': self.duration,
            'calories_burned': self.calories_burned,
            'date': self.date.isoformat(),
            'exercises': [exercise.to_dict() for exercise in self.exercises]
        }


# Main Page
@app.route('/')
def index_page():
    workouts = Workout.query.all()
    if workouts is None:
        return jsonify({'error': 'Workouts not found'}), 404

    workout_list = [workout.to_dict() for workout in workouts]
    return render_template('index.html', workout_list=workout_list)

# Create Page
@app.route('/create')
def create_page():
    return render_template('create.html')

# About Page
@app.route('/about')
def get_about_info():
    return render_template('about.html')

# Edit Page
@app.route('/edit/<int:id>')
def edit_page(id):
    workout = Workout.query.get(id)
    workout_date = workout.date.strftime('%Y-%m-%d')
    return render_template('edit.html', workout=workout, workout_date=workout_date)

#  Workout Delete Api
@app.route('/api/workout/<int:id>', methods=['DELETE'])
def delete_workout(id):
    workout = Workout.query.get(id)

    db.session.delete(workout)
    db.session.commit()

    return jsonify({'message': 'Workout deleted successfully'}), 200

# API to create a workout and exercises
@app.route('/api/workout', methods=['POST'])
def create_workout():
    workout_data = request.get_json()

    # Merge data for sql
    date = datetime.strptime(workout_data['date'], "%Y-%m-%d")
    datetime_obj = datetime.strptime(f"{date.year:04d}-{date.month:02d}-{date.day:02d} 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")

    # Create a new Workout object
    workout = Workout(
        name=workout_data['name'],
        type=workout_data['type'],
        duration=workout_data['duration'],
        calories_burned=workout_data['calories_burned'],
        date=datetime_obj
    )

    # Create Exercise objects and associate them with the workout
    exercises_data = workout_data['exercises']
    for exercise_data in exercises_data:
        exercise = Exercise(
            name     = exercise_data['name'],
            rep      = int(exercise_data['rep']) if exercise_data['rep'] != '' else None,
            weight   = float(exercise_data['weight']) if exercise_data['weight'] != '' else None,
            duration = int(exercise_data['duration']) if exercise_data['duration'] != '' else None,
            distance = float(exercise_data['distance']) if exercise_data['distance'] != '' else None
        )
        workout.exercises.append(exercise)

    # # Add the workout to the database
    db.session.add(workout)
    db.session.commit()

    # Return the workout ID
    return "Created Successful", 201

@app.route('/api/workout/<int:id>', methods=['PUT'])
def edit_workout(id):
    workout_data = request.get_json()

    workout = Workout.query.get(id)
    if workout is not None:

        # Merge data for sql
        date = datetime.strptime(workout_data['date'], "%Y-%m-%d")
        datetime_obj = datetime.strptime(f"{date.year:04d}-{date.month:02d}-{date.day:02d} 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")

        # Edit workout
        workout.name = workout_data['name']
        workout.type = workout_data['type']
        workout.duration = int(workout_data['duration'])
        workout.calories_burned = float(workout_data['calories_burned'])
        workout.date = datetime_obj
        workout.exercises.clear()

        # Create Exercise objects and associate them with the workout
        exercises_data = workout_data['exercises']
        for exercise_data in exercises_data:
            exercise = Exercise(
                name=exercise_data['name'],
                rep=int(exercise_data['rep']) if exercise_data['rep'] != '' else None,
                weight=float(exercise_data['weight']) if exercise_data['weight'] != '' else None,
                duration=int(exercise_data['duration']) if exercise_data['duration'] != '' else None,
                distance=float(exercise_data['distance']) if exercise_data['distance'] != '' else None
            )
            workout.exercises.append(exercise)

        db.session.commit()

    return "Successfully updated", 200

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    duration_filter = int(request.args.get('duration')) if request.args.get('duration') is not None else 0
    start_date_filter = request.args.get('start_date')
    end_date_filter = request.args.get('end_date')

    # Get all workouts from the database
    workouts = Workout.query.all()

    # Apply filters if provided
    if duration_filter:
        workouts = filter_workouts_by_duration(workouts, duration_filter)
    if start_date_filter and end_date_filter:
        workouts = filter_workouts_by_date_range(workouts, start_date_filter, end_date_filter)

    return jsonify([workout.to_dict() for workout in workouts]), 200


def filter_workouts_by_duration(workouts, duration_filter):
    filtered_workouts = []
    for workout in workouts:
        if workout.duration >= duration_filter:
            filtered_workouts.append(workout)
    return filtered_workouts


def filter_workouts_by_date_range(workouts, start_date_filter, end_date_filter):
    filtered_workouts = []
    start_date = datetime.strptime(start_date_filter, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_filter, "%Y-%m-%d").date() + timedelta(days=1)

    for workout in workouts:
        if start_date <= workout.date.date() < end_date:
            filtered_workouts.append(workout)
    return filtered_workouts

with app.app_context():
    db.create_all()
    #app.run()
