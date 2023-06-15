from flask import Flask, jsonify
from flask import request, render_template
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
db = SQLAlchemy(app)


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

# Main Page
@app.route('/create')
def create_page():
    return render_template('create.html')

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
    return "123", 201





















@app.route('/api/Workout/add/first/', methods=['GET'])
def create_workout_once():
    # Create a new workout instance
    workout = Workout(
        name='My Workout',
        type='Strength Training',
        duration=60,
        calories_burned=300,
        date=datetime.utcnow()
    )

    # Create a few exercise instances
    exercise1 = Exercise(
        name='Squats',
        rep=10,
        weight=50,
        duration=30,
        distance=None
    )

    exercise2 = Exercise(
        name='Push-ups',
        rep=15,
        weight=None,
        duration=10,
        distance=None
    )

    exercise3 = Exercise(
        name='Plank',
        rep=None,
        weight=None,
        duration=60,
        distance=None
    )

    # Add the exercises to the workout
    workout.exercises.extend([exercise1, exercise2, exercise3])

    # Add the workout and exercises to the database
    db.session.add(workout)
    db.session.commit()

    return jsonify(workout.to_dict()), 200


# @app.route('/workout/<int:workout_id>', methods=['GET'])
# def get_workout(workout_id):
#     # return "great no shit u here", 200
#     workout = Workout.query.get(workout_id)
#     if workout is None:
#         return jsonify({'error': 'Workout not found'}), 404
#
#     return jsonify(workout.to_dict()), 200


# @app.route('/api/Workout/<int:workout_id>', methods=['DELETE'])
# def delete_workout(workout_id):
#     workout = Workout.query.get(workout_id)
#     if workout is None:
#         return jsonify({'error': 'Workout not found'}), 404
#
#     deleted_workout = workout.to_dict()
#
#     db.session.delete(workout)
#     db.session.commit()
#
#     return jsonify({'message': 'Workout deleted successfully', 'deleted_workout': deleted_workout}), 200

@app.route('/api/Workout/<int:workout_id>', methods=['PUT'])
def update_workout(workout_id):
    workout = Workout.query.get(workout_id)
    if workout is None:
        return jsonify({'error': 'Workout not found'}), 404

    updated_details = request.json

    workout.name = updated_details.get('name', workout.name)
    workout.type = updated_details.get('type', workout.type)
    workout.duration = updated_details.get('duration', workout.duration)
    workout.calories_burned = updated_details.get('calories_burned', workout.calories_burned)

    db.session.commit()

    return jsonify({'message': 'Workout updated successfully', 'updated_workout': workout.to_dict()}), 200


@app.route('/api/Workout')
def get_workouts():
    day = request.args.get('day')
    duration = request.args.get('duration')
    workouts = Workout.query

    if day:
        workouts = workouts.filter(func.date(Workout.date) == day)
    elif duration:
        workouts = workouts.filter(Workout.duration >= duration)

    workouts = workouts.all()

    return jsonify([workout.to_dict() for workout in workouts]),


@app.route('/api/about')
def get_about_info():
    team_members = [
        {'name': 'Davit Gogilashvili', 'surname': 'Gogilashvili'},
        {'name': 'Davit Purtseladze', 'surname': 'Purtseladze'},
        {'name': 'Dimitri Chakvetadze', 'surname': 'Chakvetadze'},
        {'name': 'Nika Gavardashvili', 'surname': 'Gavardashvili'},
        {'name': 'Mariam Metreveli', 'surname': 'Metreveli'}
    ]

    description = "The Fitness App is a comprehensive fitness tracker designed to help you monitor and manage your workouts. " \
                  "It allows you to create and track your workout routines, record exercise details, track calories burned, and view your progress over time."

    about_info = {
        'team_number': 9,
        'team_members': team_members,
        'description': description
    }

    return jsonify(about_info)


with app.app_context():
    db.create_all()
    app.run()
