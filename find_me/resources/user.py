from flask_restful import Resource, reqparse
from mysql.connector import connect
from flask import jsonify

class User(Resource):
    def __init__(self):
        self.db = connect(
            host='localhost',
            user='denizkazici',
            password='password',
            database='project'
        )

        self.cursor = self.db.cursor()
        
    def get(self, user_id):
        self.cursor.execute(f"SELECT * FROM user WHERE user_id={user_id}")
        result = self.cursor.fetchone()

        if not result:
            return {'message': 'User not found'}, 404

        user = {
            'user_id': result[0],
            'name': result[1],
            'password': result[2],
            'team_id': result[3],
            'age': result[4],
            'info': result[5],
            'lat': result[6],
            'lng': result[7],
            'created_at': result[8],
            'updated_at': result[9],
            'building_id': result[10],
            'user_type': result[11]
        }
        response = jsonify(user)
        response.status_code = 200 
        return response

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=False)
        parser.add_argument('password', required=False)
        parser.add_argument('team_id', required=False)
        parser.add_argument('age', required=False)
        parser.add_argument('info', required=False)
        parser.add_argument('lat', required=False)
        parser.add_argument('lng', required=False)
        parser.add_argument('building_id', required=False)
        parser.add_argument('user_type', required=False)
        args = parser.parse_args()
        

        sql = "INSERT INTO user (name, password, team_id, age, info, lat, lng, building_id, user_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (args['name'], args['password'], args['team_id'], args['age'], args['info'], args['lat'], args['lng'], args['building_id'], args['user_type'])
        self.cursor.execute(sql, val)
        self.db.commit()

        return {'message': 'User created successfully'}, 200
    
    def put(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('password')
        parser.add_argument('team_id')
        parser.add_argument('age')
        parser.add_argument('info')
        parser.add_argument('lat')
        parser.add_argument('lng')
        parser.add_argument('building_id')
        args = parser.parse_args()

        updates = []
        for key in args.keys():
            if args[key]:
                updates.append(f"{key}='{args[key]}'")

        if not updates:
            return {'message': 'No updates provided'}, 400

        update_string = ', '.join(updates)

        self.cursor.execute(f"SELECT * FROM user WHERE user_id={user_id}")
        result = self.cursor.fetchone()
        if not result:
            return {'message': 'User not found'}, 404

        self.cursor.execute(f"UPDATE user SET {update_string} WHERE user_id={user_id}")
        self.db.commit()

        return {'message': 'User updated successfully'}, 200
        
    def delete(self, user_id):
        self.cursor.execute(f"SELECT * FROM user WHERE user_id={user_id}")
        result = self.cursor.fetchone()

        if not result:
            return {'message': 'User not found'}, 404

        self.cursor.execute(f"DELETE FROM user WHERE user_id={user_id}")
        self.db.commit()

        return {'message': 'User deleted successfully'}, 200

    def __del__(self):
        self.db.close() 
        



        