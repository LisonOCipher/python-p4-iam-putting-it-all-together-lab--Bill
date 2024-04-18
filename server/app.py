#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    
    def post(self):
        json_data = request.get_json()
        if not json_data:
            return {'message': 'No input data provided'}, 400

        username = json_data.get('username')
        password = json_data.get('password')
        image_url = json_data.get('image_url', '')
        bio = json_data.get('bio', '')

        if not username or not password:
            return {'message': 'Username and password are required'}, 422
        
        try:
            user = User(username=username, image_url=image_url, bio=bio)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return jsonify(user=user.to_dict()), 201
        except IntegrityError:
            db.session.rollback()
            return {'message': 'Username already exists'}, 422
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 500

class CheckSession(Resource):
    
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return jsonify(user=user.to_dict()), 200
        return {'message': 'Unauthorized'}, 401

class Login(Resource):
    
    def post(self):
        json_data = request.get_json()
        if not json_data:
            return {'message': 'No input data provided'}, 400
        
        username = json_data.get('username')
        password = json_data.get('password')
        
        if not username or not password:
            return {'message': 'Username and password are required'}, 422
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return jsonify(user=user.to_dict()), 200
        return {'message': 'Invalid username or password'}, 401

class Logout(Resource):
    
    def delete(self):
        session.pop('user_id', None)
        return {}, 204

class RecipeIndex(Resource):
    
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'message': 'Unauthorized'}, 401
        
        recipes = Recipe.query.filter_by(user_id=user_id).all()
        return jsonify(recipes=[recipe.to_dict() for recipe in recipes]), 200
    
    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'message': 'Unauthorized'}, 401
        
        json_data = request.get_json()
        if not json_data:
            return {'message': 'No input data provided'}, 400
        
        title = json_data.get('title')
        instructions = json_data.get('instructions')
        minutes_to_complete = json_data.get('minutes_to_complete')
        
        if not title or not instructions or len(instructions) < 50:
            return {'message': 'Title and instructions (at least 50 characters) are required'}, 422
        
        recipe = Recipe(title=title, instructions=instructions, minutes_to_complete=minutes_to_complete, user_id=user_id)
        db.session.add(recipe)
        db.session.commit()
        
        return jsonify(recipe=recipe.to_dict()), 201

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
