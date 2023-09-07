from flask import Flask, jsonify, request
import requests, time
from datetime import datetime
from threading import Lock
import time
import decimal
from flask_restful import Api
import mysql.connector
import random, math
from typing import List
from resources.user import User
from resources.team import team
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN
import numpy as np
from sklearn.metrics import silhouette_score


app = Flask(__name__)
api = Api(app)
lock = Lock()
lockcomplete = Lock()
silivri_lat = 41.0730
silivri_long = 28.2466

api_key = "AIzaSyC1xMDHjip4lmhoUChAGtS9nFqLBfjZHWg"
max = 24
min = 8

mydb = mysql.connector.connect(
  host="localhost",
  user="denizkazici",
  password="password",
  database="project"
)
api = Api(app)
api.add_resource(User, '/user/<int:user_id>', '/user')
api.add_resource(team, '/user/<int:team_id>')
####
cursor = mydb.cursor()

@app.route('/teamList')
def teamlist():
  cursor.execute("SELECT * FROM team")
  rows = cursor.fetchall()
  teams = []
  for row in rows:
    team = {
      'team_id': row[0],
      'name': row[1],
      'lat': row[2],
      'lng' : row[3],
      'created_at' : row[4],
      'updated_at' : row[5],
      'building_id' : row[6],
      'count' : row[7]
    }
    teams.append(team)
  response = jsonify(teams)
  response.status_code = 200 
  return response

@app.route('/roadList')
def roadlist():
  cursor.execute("SELECT * FROM road")
  rows = cursor.fetchall()
  roads = []
  for row in rows:
    road = {
      'road_id': row[0],
      'name': row[1],
      'lat': row[2],
      'lng' : row[3],
      'created_at' : row[4],
      'updated_at' : row[5]
    }
    roads.append(road)
 
  response = jsonify(roads)
  response.status_code = 200 
  return response

@app.route('/buildingList')
def buildinglist():
  cursor.execute("SELECT * FROM building")
  columns = [column[0] for column in cursor.description]
  data = cursor.fetchall()
  buildings = []
  for row in data:
    buildings.append(dict(zip(columns, row))) 
  response = jsonify(buildings)
  response.status_code = 200 
  return response

@app.route('/groupList')
def groupList():
  cursor.execute("SELECT id, group_table.group_id, building_id , group_table.created_at, group_table.updated_at, range_value FROM building_group INNER JOIN group_table ON building_group.group_id = group_table.group_id")
  columns = [column[0] for column in cursor.description]
  data = cursor.fetchall()
  result = []
  for row in data:
    result.append(dict(zip(columns, row)))
  return jsonify(result)
  
  
@app.route('/groupedList') #aynı grupta bulunan binaların listesi
def groupedList():
  grouped_id = request.args.get('id')
  buildingList = getGroupedBuildings(grouped_id, 0)
  print(len(buildingList))
  resultList = []
  
  for building in buildingList:
    print("3")
    if building.matches == 0 and building.completed == 0:
      
      build = {
        'building_id': building.building_id,
        'name': building.name,
        'address': building.address,
        'lat' : building.lat,
        'lng' : building.lng,
        'created_at' : building.created_at,
        'updated_at' : building.updated_at,
        'count' : building.count,
        'matches' : building.matches,
        'completed' : building.completed,
        'person_count' : building.person_count,
        'group_id' : grouped_id,
        'group_count' : len(buildingList)
      }
      resultList.append(build)
  
  if len(resultList) == 0:
    return {"message": "No matching building found"}, 400
  response = jsonify(resultList)
  response.status_code = 200 
  return response
  
  
@app.route('/userList')
def userlist():
  cursor.execute("SELECT * FROM user")
  rows = cursor.fetchall()
  print(rows)
  users = []
  for row in rows:
    user = {
      'user_id': row[0],
      'name': row[1],
      'password': row[2],
      'team_id': row[3],
      'age': row[4],
      'info': row[5],
      'lat': row[6],
      'lng': row[7],
      'created_at': row[8],
      'updated_at': row[9],
      'building_id': row[10],
      'user_type': row[11],    
    }
    users.append(user)
  response = jsonify(users)
  response.status_code = 200 
  return response
  
@app.route('/updateUser')
def updateUser():
  lat = request.args.get('lat')
  lng = request.args.get('lng')
  id = request.args.get('id')
  cursor.execute("UPDATE user SET lat = %s, lng = %s WHERE user_id = %s", (lat, lng, id,))
  mydb.commit()
  return {"message": "location updated"}, 200
  
@app.route('/login' , methods=['POST'])
def login():
  name = request.json.get('name')
  password = request.json.get('password')
  cursor.execute("SELECT * FROM user WHERE name = %s", (name,))
  result = cursor.fetchone()
  if result is not None:
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
      'user_type': result[11],    
    }
    
    if user:
      if user['password'] == password:
        response = jsonify(user)
        response.status_code = 200 
        return response
      else:
        return jsonify({'message': 'Invalid password'}), 401
  else:
    user = {
      'user_id': 1,
      'name': "test",
      'password': "jf",
      'team_id': 4,
      'age': 4,
      'info': "kj",
      'lat': 1,
      'lng': 1,
      'created_at': "klt",
      'updated_at': "kk",
      'building_id': 1,
      'user_type': 1,    
    }
    response = jsonify(user)
    response.status_code = 200 
    return response
  
@app.route('/distance')
def distance():
  lock.acquire()
  try:
    
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    merkezlat =request.args.get('merkezlat')
    merkezlng = request.args.get('merkezlng')
    distance = request.args.get('distance')
    find_distance = calculate_distance(lat, lng, merkezlat, merkezlng) 
    if int(distance) > find_distance: 
      print(find_distance)
      return {"message": f"{find_distance}"}, 200
    return {"message": "not yet"}, 400
  finally:
    lock.release()
@app.route('/createDistance')
def createDistance():
  merkezlat =request.args.get('merkezlat')
  merkezlng = request.args.get('merkezlng') 
  distance = request.args.get('distance')
  lat, lng = createLatLong(merkezlat, merkezlng, distance, 1)
  return {"message": f"{lat}-{lng}"}, 200

def createLatLong (lat, lng, limit, check):
  #if check = 1 create lat long for team 
  yon = random.uniform(0, 360)
  if check:
    mesafe = int(limit)
  else:
    mesafe = random.uniform(0, limit)
  R = 6371000  
  d = mesafe / R  
  lat1 = math.radians(float(lat))
  lon1 = math.radians(float(lng))
  lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(math.radians(yon)))
  lon2 = lon1 + math.atan2(math.sin(math.radians(yon)) * math.sin(d) * math.cos(lat1), math.cos(d) - math.sin(lat1) * math.sin(lat2))
  random_lat = math.degrees(lat2)
  random_long = math.degrees(lon2)
  return random_lat, random_long


@app.route('/algorithm')
def algorithm():
  lat = request.args.get('lat')
  lng = request.args.get('long')
  id = request.args.get('id')
  result_building = None
  ## begin the algorithm : 
 
  lock.acquire()
  try:
    cursor.execute(f"SELECT * FROM team WHERE team_id={id}")
    result = cursor.fetchone()
    if not result:
      return {'message': 'Team not found'}, 404
    team = Team(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
    if not lat and not lng:
      lat = team.lat
      lng = team.lng
  
    cursor.execute("SELECT COUNT(*) FROM team WHERE building_id IS NOT NULL")
    team_count = int(cursor.fetchone()[0]) #team count
    ## building list 
  
    cursor.execute("SELECT * FROM building WHERE matches = 0 and completed = 0 and created_at = (SELECT MIN(created_at) FROM building);")
    results = cursor.fetchall()
    building_list = []
    building_time_list = []
    groupId = 0
    groupCount = 0
  
    for row in results:
      building = Building(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
      building_list.append(building)
  
    if len(building_list) == 0: 
    ## building size == 0  case
      count = team.count
      tmp = max - count
      cursor.execute("SELECT * FROM building WHERE matches = 1 and completed = 0 and count < %s", (tmp,))
      results = cursor.fetchall()
      building_list = []
      for row in results:
        building = Building(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
        building_list.append(building)
      if len(building_list) > 0:
        result_building, building_time_list=calculate_time(lat, lng, building_list, building_time_list)
      else : 
        return {'message': 'All buildings completed'}, 400
    else:
      sql = "SELECT group_id FROM building_group"
      cursor.execute(sql)
      group_ids = [row[0] for row in cursor.fetchall()] 
      if team_count < len(group_ids): 
        print("ALGORİTHM GRUP:::")
        print(team_count)
        print(len(group_ids))
        groupedList: List[Building]= []
        for group_id in group_ids: ##her grubun içinden gitme mesafesi en kısa olan binayı buldum 
          groupedBuilding: List[Building] = getGroupedBuildings(group_id, 2)
          
          if len(groupedBuilding) > 1:
            value ,building_time_list = calculate_time(lat, lng, groupedBuilding, building_time_list)
            print("building_time_list:", building_time_list)
            if value != -1:
              print("hatasız")
              groupedList.append({'id': value['id'], 'time': value['time'], 'group_id': group_id , 'road' : value['road']})
        if len(groupedList) > 0:
          sorted_list = sorted(groupedList, key=lambda x: x['time'])
          result_building = sorted_list[0]
          groupId = result_building['group_id']
    ## group kısmı bitti
      else:
        result_building, building_time_list=calculate_time(lat, lng, building_list, building_time_list)
  #return için
  
    if result_building != -1 and result_building is not None:
      first_id = result_building['id']
      time_value = result_building['time'] 
      destroyedRoad = result_building['road']
      matching_building = None
      for building in building_list:
        if building.building_id == first_id:
          matching_building = building
          break
      if matching_building:
        building_count = matching_building.count + team.count
        cursor.execute("UPDATE building SET matches = 1, count = %s WHERE building_id = %s", (building_count, matching_building.building_id,))
        cursor.execute("UPDATE team SET building_id = %s WHERE team_id = %s", (matching_building.building_id, team.team_id,))
      
        if cursor.rowcount > 0:
          print("Güncelleme başarılı. Etkilenen satır sayısı:", cursor.rowcount)
        else:
          print("Güncelleme başarısız. Hiçbir satır etkilenmedi.")
        mydb.commit()
        if groupId == 0 : # gruplandırma yok
          groupId = matching_building.group_id
        else: 
          buildingList = getGroupedBuildings(groupId, 1)
          for building in buildingList:
            cursor.execute("UPDATE building SET group_id = %s WHERE building_id = %s", (groupId, building.building_id,))
            if cursor.rowcount > 0:
              print("Güncelleme başarılı. Etkilenen satır sayısı:", cursor.rowcount)
            else:
              print("Güncelleme başarısız. Hiçbir satır etkilenmedi.")
          groupCount = len(buildingList)
          cursor.execute("UPDATE building SET group_id = %s WHERE building_id = %s", (groupId, matching_building.building_id,))
          mydb.commit()
        build = {
          'building_id': matching_building.building_id,
          'name': matching_building.name,
          'address': matching_building.address,
          'lat' : matching_building.lat,
          'lng' : matching_building.lng,
          'created_at' : matching_building.created_at,
          'updated_at' : matching_building.updated_at,
          'count' : team.count,
          'matches' : 1,
          'completed' : matching_building.completed,
          'person_count' : matching_building.person_count,
          'group_id' : groupId,
          'time' : time_value,
          'group_count' : groupCount,
          'road' : destroyedRoad
          }
        response = jsonify(build)
        response.status_code = 200 
        return response
        
      return {'message': 'No matching found'}, 400
    return {'message': 'No matching found'}, 400
  finally:
    lock.release()

@app.route('/getBuilding')
def getBuilding():
  lat = request.args.get('lat')
  lng = request.args.get('long')
  group_id = request.args.get('group_id')
  team_id = request.args.get('team_id')
  lock.acquire()
  try :
    cursor.execute(f"SELECT * FROM team WHERE team_id={team_id}")
    result = cursor.fetchone()
    if not result:
      return {'message': 'Team not found'}, 404
  
    building_list = []
    building_time_list = [] 
    team = Team(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
    cursor.execute("SELECT COUNT(*) FROM team WHERE building_id IS NOT NULL")
    team_count = int(cursor.fetchone()[0]) #team count
    cursor.execute("SELECT * FROM building WHERE matches = 0 and completed = 0 and created_at = (SELECT MIN(created_at) FROM building);")
    results = cursor.fetchall()
  
    for row in results:
      building = Building(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
      building_list.append(building)
    
    result_building = None
    if team_count < (len(building_list) / 2):
      groupedBuilding: List[Building] = getGroupedBuildings(group_id, 2)
        # Başlangıçta None olarak tanımlanıyor
      if len(groupedBuilding) >= 1:
        result_building ,building_time_list = calculate_time(lat, lng, groupedBuilding, building_time_list)
      
    if result_building != -1 and result_building is not None:
      first_id = result_building['id']
      time_value = result_building['time'] 
      destroyedRoad = result_building['road']
      matching_building = None
      for building in groupedBuilding:
        if building.building_id == first_id:
          matching_building = building
          break
      if matching_building:
        building_count = matching_building.count + team.count
        cursor.execute("UPDATE building SET matches = 1, count = %s WHERE building_id = %s", (building_count, matching_building.building_id,))
        cursor.execute("UPDATE team SET building_id = %s WHERE team_id = %s", (matching_building.building_id, team.team_id,))
        if cursor.rowcount > 0:
          print("Güncelleme başarılı. Etkilenen satır sayısı:", cursor.rowcount)
        else:
          print("Güncelleme başarısız. Hiçbir satır etkilenmedi.")
        mydb.commit()
    
      
        groupCount = len(groupedBuilding) - 1
        
        build = {
          'building_id': matching_building.building_id,
          'name': matching_building.name,
          'address': matching_building.address,
          'lat' : matching_building.lat,
          'lng' : matching_building.lng,
          'created_at' : matching_building.created_at,
          'updated_at' : matching_building.updated_at,
          'count' : team.count,
          'matches' : 1,
          'completed' : matching_building.completed,
          'person_count' : matching_building.person_count,
          'group_id' : group_id,
          'time' : time_value,
          'group_count' : groupCount,
          'road' : destroyedRoad
          }
        response = jsonify(build)
        response.status_code = 200 
        return response
        
    return {'message': 'No matching found'}, 400
  finally:
    lock.release()
      
      
      
class Building:
    def __init__(self, id, name, address, lat, lng, created_at, updated_at, count, group_id, matches, completed, person_count):
        self.building_id = id
        self.name = name
        self.address = address
        self.lat = lat
        self.lng = lng
        self.created_at = created_at
        self.updated_at = updated_at
        self.count = count
        self.group_id = group_id
        self.matches = matches
        self.completed = completed
        self.person_count = person_count
    def __str__(self):
        return f"Building ID: {self.building_id}, Name: {self.name}"
class Team:
  def __init__(self, id, name, lat, lng, created_at, updated_at, building_id, count):
    self.team_id = id
    self.name = name
    self.lat = lat
    self.lng = lng
    self.created_at = created_at
    self.updated_at = updated_at
    self.building_id = building_id
    self.count = count
class Road:
    def __init__(self, id, name, lat, lng, created_at, updated_at):
        self.road_id = id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.created_at = created_at
        self.updated_at = updated_at
        
# Haversine formülü  metre döndürüyor 
def calculate_distance(lat1, lng1, lat2, lng2):
  lat1 = decimal.Decimal(lat1)
  lng1 = decimal.Decimal(lng1)
  lat2 = decimal.Decimal(lat2)
  lng2 = decimal.Decimal(lng2)
  R = 6371000  
  dLat = math.radians(lat2 - lat1)
  dLon = math.radians(lng2 - lng1)
  a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  distance = R * c
  return distance
  


def find_min(lat , lng, building_list: List[Building]):
  min_distance = float('inf')
  for building in building_list:
    distance = calculate_distance(lat, lng, building.lat, building.lng)
    if distance < min_distance:
      min_distance = distance
  return min_distance 

  
def calculate_time(lat, lng, building_list: List[Building], building_time_list ):
  print("calculate time")
  cursor = mydb.cursor()
  cursor.execute("SELECT * FROM road") 
  results = cursor.fetchall()
  destroyed_list = []
  for row in results:
    road = Road(row[0], row[1], row[2], row[3], row[4], row[5])
    destroyed_list.append(road)
  sorted_list=[]
  
  for building in building_list:
    if(any(item['id'] == building.building_id for item in building_time_list)):
      print("id bulundu:")
      
    else:
      url = f"https://maps.googleapis.com/maps/api/directions/json?origin={lat},{lng}&destination={building.lat},{building.lng}&key={api_key}"
      response = requests.get(url)
      data = response.json()
      ##destoryed list boş olduğunda
      if len(destroyed_list) == 0:
        print("LİSTEEEEEEE")
        duration_value = data['routes'][0]['legs'][0]['duration']['value'] # 658
        building_time_list.append({'id': building.building_id, 'time': duration_value, 'road' : "no destroyed" })
      else:
        road_found = False
        if 'routes' not in data or len(data['routes']) == 0:
          return -1, building_time_list
        steps = data["routes"][0]["legs"][0]["steps"]
        for step in steps:
          for road in destroyed_list:
            keyword = road.name
          ## yıkılan yol varsa: 
            if keyword in step["html_instructions"]:
              #keyword destroyed List
              r_lat = step['start_location']['lat']
              r_lng = step['start_location']['lng']
              url = f"https://maps.googleapis.com/maps/api/directions/json?origin={lat},{lng}&destination={r_lat},{r_lng}&key={api_key}"
              response = requests.get(url)
              data = response.json()
              time_value = data['routes'][0]['legs'][0]['duration']['value'] 
              r_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={r_lat},{r_lng}&destination={building.lat},{building.lng}&key={api_key}&mode=walking"
              response = requests.get(r_url)
              r_data = response.json()
              remainder_value = r_data['routes'][0]['legs'][0]['duration']['value'] 
              time = time_value + remainder_value
              building_time_list.append({'id': building.building_id, 'time': time , 'road' : keyword})
              road_found = True
            if road_found:  # Eğer yolu bulduysa, döngüden çık
              break
      
        if not road_found: 
          duration_value = data['routes'][0]['legs'][0]['duration']['value'] # 658
          building_time_list.append({'id': building.building_id, 'time': duration_value, 'road' : "no destroyed"})
              
  sorted_list = sorted(building_time_list, key=lambda x: x['time'])
  

  print("sorted_list:", sorted_list)
  if len(sorted_list)==0 :
    return -1, building_time_list
  return sorted_list[0] , building_time_list

@app.route('/createDestroyedList')
def destroyedList():
  id = request.args.get('id')
  cursor.execute(f"SELECT * FROM team WHERE team_id={id}")
  result = cursor.fetchone()
  if not result:
    return {'message': 'team not found'}, 404
  team = Team(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7])
  lat = team.lat
  lng = team.lng
  cursor.execute("SELECT * FROM building") #tüm binaları alıyor
  results = cursor.fetchall()
  building_list = []
  for row in results:
    building = Building(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
    building_list.append(building)
  for building in building_list:
    value = random.randint(0, 1)
    if(value): # o binanın path'i içinde yıkılmış yol bulunup bulunmayacağı
      url = f"https://maps.googleapis.com/maps/api/directions/json?origin={lat},{lng}&destination={building.lat},{building.lng}&key={api_key}"
      print(lat)
      print(lng)
      print(building.lat)
      print(building.lng)
      response = requests.get(url)
      data = response.json()
      if 'routes' not in data or len(data['routes']) == 0:
         return {'message': 'data hatası'}, 200
      steps=data['routes'][0]['legs'][0]['steps']
      step_count = len(steps)
      rndm= random.randint(0, step_count-1)
      road_name = steps[rndm]["html_instructions"]
      road_lat = steps[rndm]['start_location']['lat']
      road_lng = steps[rndm]['start_location']['lng']
      sql = "INSERT INTO road (name, lat, lng) VALUES (%s, %s, %s);"
      val = (road_name, road_lat, road_lng)
      cursor.execute(sql, val)
      mydb.commit()
  return {'message': f'Destroyed road table created for {id}'}, 200
#### ADMIN ###
@app.route('/adminBuildingList')
def createBuildingList():
  merkezlat = request.args.get('merkezlat')
  merkezlng = request.args.get('merkezlng')
  distance = int(request.args.get('distance'))
  count = int(request.args.get('count'))
  setEarthquake(merkezlat, merkezlng, distance)
  geolocator = Nominatim(user_agent="my_flask_app")
  cursor = mydb.cursor()
  timestamp = int(time.time())
  dt = datetime.fromtimestamp(timestamp)
  current_time = dt.strftime('%Y-%m-%d %H:%M:%S')
  for i in range(count):
    lat , long = createLatLong(merkezlat, merkezlng, distance, 0)
    location = geolocator.reverse((lat, long))
    address = location.address
    raw_data = location.raw
    display_name = raw_data['display_name']
    town = raw_data['address'].get('town', 'N/A')
    sql = "INSERT INTO building (name, address, count, person_count, lat, lng, matches, completed, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s,%s, %s)"
    val = (town, address , 0, 0, lat, long, 0, 0, current_time)
    cursor.execute(sql, val)
    mydb.commit()
  return {'message': 'admin tarafından building table created'}, 200

@app.route('/createBuildingList')
def add_building():
  geolocator = Nominatim(user_agent="my_flask_app")
  cursor = mydb.cursor()
  timestamp = int(time.time())
  dt = datetime.fromtimestamp(timestamp)
  current_time = dt.strftime('%Y-%m-%d %H:%M:%S')
  for i in range(100):
    lat , long = createLatLong(silivri_lat, silivri_long, 5000, 0)
    location = geolocator.reverse((lat, long))
    address = location.address
    raw_data = location.raw
    display_name = raw_data['display_name']
    town = raw_data['address'].get('town', 'N/A')
    sql = "INSERT INTO building (name, address, count, person_count, lat, lng, matches, completed, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s,%s, %s)"
    val = (town, address , 0, 0, lat, long, 0, 0, current_time)
    cursor.execute(sql, val)
    mydb.commit()
  return {'message': 'building table created'}, 200

@app.route('/createUserList')
def add_user():
  cursor.execute("SELECT * FROM building") #tüm binaları alıyor
  results = cursor.fetchall()
  building_list = []
  for row in results:
    building = Building(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
    building_list.append(building)
    
  for building in building_list:
    random_count = random.randint(1,3)
    for j in range(random_count):
      random_age = random.randint(18, 70)
      sql = "INSERT INTO user (name, password, lat , lng,  building_id, age, info, user_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
      val = ("user", "user", building.lat, building.lng, building.building_id, random_age, "info", 0)
      cursor.execute(sql, val)
      cursor.execute("UPDATE building SET person_count = %s WHERE building_id = %s", (random_count, building.building_id,))
      mydb.commit()
  return {'message': 'user table created'}, 200

  
@app.route('/adminTeamList')
def add_team():
  merkezlat = float(request.args.get('merkezlat'))
  merkezlng = float(request.args.get('merkezlng'))
  distance = request.args.get('distance')
  teamCount = int(request.args.get('count'))
  if not merkezlat and not merkezlng and not distance and teamCount:
    return {'error': 'missing value lat, lng, distance, count'}, 200
  for i in range(teamCount):
    lat , long = createLatLong(merkezlat, merkezlng, distance, 1)
    random_count = random.randint(8, 10)
    sql = "INSERT INTO team (name, lat, lng, count) VALUES (%s, %s, %s, %s)"
    val = ("teamName", lat, long, random_count)
    cursor.execute(sql, val)
    team_id = cursor.lastrowid
    mydb.commit()

    for j in range(random_count):
      random_age = random.randint(18, 70)
      sql = "INSERT INTO user (name, password, lat, lng, team_id, age, info, user_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
      val = ("teamuser", "teamuser", lat, long,  team_id, random_age, "info", 1)
      cursor.execute(sql, val)
      mydb.commit()
  return {'message': 'admin team table created'}, 200
  
@app.route('/createGroupList') 
def group_distance():
  cursor.execute("SELECT * FROM building WHERE matches = 0 and completed = 0")
  results = cursor.fetchall()
  building_list = []
  for row in results:
    building = Building(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
    building_list.append(building)
      
  coordinates = np.array([(building.lat, building.lng) for building in building_list])
      
  eps , min_samples = update_eps_min_samples(building_list)
  dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine')
  labels = dbscan.fit_predict(coordinates)
  
  grouped_buildings = {}
  for i, label in enumerate(labels):
    if label in grouped_buildings:
      grouped_buildings[label].append(building_list[i])
    else:
      grouped_buildings[label] = [building_list[i]]
  
  
  for group_id, buildings in grouped_buildings.items():
    if len(buildings) > 1:
      
      sql = "INSERT INTO building_group (name, range_value) VALUES (%s, %s)"
      val = (str(group_id), int(len(buildings)))
      cursor.execute(sql, val)
      mydb.commit()
            
      # En son eklenen grup ID'sini al
      cursor.execute("SELECT group_id FROM building_group ORDER BY group_id DESC LIMIT 1")
      result = cursor.fetchone()
      group_id = result[0]
            
      # Group Table'a grup üyelerini ekle
      for building in buildings:
        sql = "INSERT INTO group_table (group_id, building_id) VALUES (%s, %s)"
        val = (group_id, building.building_id)
        cursor.execute(sql, val)
  return {'message': f'created group List'}, 200
    
    
  

def update_eps_min_samples(building_list):
  data = np.array([[float(building.lat), float(building.lng)] for building in building_list])
  eps_values = np.arange(0.001, 0.01, 0.001)  
  min_samples_values = np.arange(2, 7)  
  best_eps = None
  best_min_samples = None
  best_silhouette_score = -1

  for eps in eps_values:
    for min_samples in min_samples_values:
      dbscan = DBSCAN(eps=eps, min_samples=min_samples)
      clusters = dbscan.fit_predict(data)
      if len(np.unique(clusters)) > 1:
        silhouette = silhouette_score(data, clusters)
        if silhouette > best_silhouette_score:
          best_silhouette_score = silhouette
          best_eps = float(eps)  
          best_min_samples = int(min_samples) 

  return best_eps, best_min_samples

@app.route('/deleteDataset')
def delete():
  cursor.execute("UPDATE group_table SET group_id=null, building_id = null WHERE id>0")
  
  
  cursor.execute("DELETE FROM group_table WHERE id > 0")
  
  cursor.execute("ALTER TABLE group_table AUTO_INCREMENT = 1")
  
  cursor.execute("DELETE FROM building_group WHERE group_id > 0")
  cursor.execute("ALTER TABLE building_group AUTO_INCREMENT = 1")
  cursor.execute("UPDATE user SET team_id = null , building_id = null Where user_id>0")
  cursor.execute("UPDATE team SET building_id = null where team_id>0")
  cursor.execute("DELETE FROM building WHERE building_id > 0") #
  cursor.execute("ALTER TABLE building AUTO_INCREMENT = 1")
  cursor.execute("DELETE FROM road WHERE road_id > 0")
  cursor.execute("ALTER TABLE road AUTO_INCREMENT = 1")
  mydb.commit()
  
  cursor.execute("DELETE FROM user WHERE user_id>2")
  cursor.execute("ALTER TABLE user AUTO_INCREMENT = 2")
  cursor.execute("DELETE FROM team WHERE team_id > 0")
  cursor.execute("ALTER TABLE team AUTO_INCREMENT = 1")
  mydb.commit()

  return {'message': 'deleted'}, 200

def getGroupedBuildings(id, check):
  #check = 1 for algorithm
  groupedBuilding : Building = []
  sql = "SELECT building_id FROM group_table WHERE group_id=%s"
  val = tuple([id])
  cursor.execute(sql, val)
  building_ids = [row[0] for row in cursor.fetchall()] 
  
  for b_id in building_ids:
    if (check == 1) or (check == 2)  :
      sql = "SELECT * FROM building WHERE building_id=%s and matches=0"
    else : 
      sql = "SELECT * FROM building WHERE building_id=%s"
    val = tuple([b_id])
    cursor.execute(sql, val)
    results = cursor.fetchall()
    if results : 
      for row in results:
        building = Building(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
        if (check == 1):
          if building.group_id is None:
            groupedBuilding.append(building) 
        else: 
          groupedBuilding.append(building) 
  return groupedBuilding

  
@app.route('/setCompleted')
def setCompleted():
  teamId = request.args.get('team_id')
  buildingId = int(request.args.get('building_id'))
  lock.acquire()
  try:
    cursor.execute("SELECT building_id FROM team WHERE team_id = %s", (teamId,)) 
    result = cursor.fetchone()
    if result[0] is not None:
      building_id = int(result[0])
      if building_id == buildingId :
        cursor.execute("UPDATE building SET completed = 1 WHERE building_id = %s", (buildingId,))
        cursor.execute("UPDATE team SET building_id = null WHERE team_id = %s", (teamId,))
        mydb.commit()
        return {'message': f'completed {buildingId}'}, 200
    return {'message': 'hata'}, 400
  finally:
    lock.release()

@app.route('/change')
def changeNamePass():
  id = request.args.get('id')
  name = request.args.get('name')
  password = request.args.get('password')
  cursor.execute("UPDATE user SET name = %s , password = %s WHERE user_id = %s", (name, password, id, ))
  mydb.commit()
  if cursor.rowcount > 0:
    return {'message': 'Update successful'}, 200
  else:
    return {'message': 'No rows affected'}, 400
  
@app.route('/setEarthquake')
def set_earthquake():
  merkez_lat = request.args.get('merkez_lat')
  merkez_lng = request.args.get('merkez_lng')
  distance = request.args.get('distance')
    
  cursor.execute("SELECT COUNT(*) FROM earthquake")
  count = int(cursor.fetchone()[0])
    
  if count == 0:
    
    sql = "INSERT INTO earthquake (merkez_lat, merkez_lng, distance) VALUES (%s, %s, %s)"
    val = (merkez_lat, merkez_lng, distance)
    cursor.execute(sql, val)
  else:
   
    sql = "UPDATE earthquake SET merkez_lat = %s, merkez_lng = %s, distance = %s"
    val = (merkez_lat, merkez_lng, distance)
    cursor.execute(sql, val)
    
  mydb.commit()
    
  return jsonify({'message': 'Earthquake data updated successfully'})

def setEarthquake(merkez_lat, merkez_lng, distance):
  cursor = mydb.cursor()
  cursor.execute("SELECT COUNT(*) FROM earthquake")
  count = int(cursor.fetchone()[0])
  if count == 0:
    
    sql = "INSERT INTO earthquake (merkez_lat, merkez_lng, distance) VALUES (%s, %s, %s)"
    val = (merkez_lat, merkez_lng, distance)
    cursor.execute(sql, val)
  else:
    
    sql = "UPDATE earthquake SET merkez_lat = %s, merkez_lng = %s, distance = %s"
    val = (merkez_lat, merkez_lng, distance)
    cursor.execute(sql, val)
  mydb.commit()

@app.route('/getEarthquake')
def get_earthquake():
    
  cursor.execute("SELECT * FROM earthquake")
  result = cursor.fetchone()
    
  if result is None:
    return {'message': 'No earthquake data found'}, 400
    
    
  earthquake = {
    'id': result[0],
    'merkez_lat': result[1],
    'merkez_lng': result[2],
    'distance': result[3]
  }
  return jsonify(earthquake)

@app.route('/deleteEarthquake')
def delete_earthquake():
    
    
    cursor.execute("DELETE FROM earthquake")
    cursor.execute("ALTER TABLE earthquake AUTO_INCREMENT = 1;")
    mydb.commit()
    
    return jsonify({'message': 'Earthquake data deleted successfully'})

if __name__ == "__main__":
    app.run(debug=True) 