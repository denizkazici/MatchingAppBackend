from flask_restful import Resource, reqparse
from mysql.connector import connect
from flask import jsonify

class team(Resource):
    def __init__(self):
        self.db = connect(
            host='localhost',
            user='denizkazici',
            password='password',
            database='project'
        )

        self.cursor = self.db.cursor()
  
        