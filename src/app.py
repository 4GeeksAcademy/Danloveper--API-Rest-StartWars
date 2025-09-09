"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite, Vehicle
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints

def get_registers(class_name, info_name):
    try:
        data = db.session.execute(db.select(class_name)).scalars().all()
        data_list = [record.serialize() for record in data]
        return {info_name: data_list}, 200
    except Exception as error:
        print(error)
        return {'msg': 'Ocurrio un error', 'error': error}, 500
    
def get_register_by_id(class_name, filter_id, filter_name):
    try:
        if not filter_id.isdigit():
            return {'msg': f'la busqueda del registro debe ser el id del {filter_name}'}, 400
        filter = int(filter_id)
        data_filter = db.session.execute(db.select(class_name).filter_by(id=filter)).scalar_one_or_none()
        if not data_filter:
            return {'msg': f'No se encontro {filter_name} con el id {filter_id}'}, 404
        return {filter_name: data_filter.serialize()}, 200
    except Exception as err:
        return {'msg': 'Ha ocurrido un error con la solicitud', 'error': err}, 500
    
def validate_favorite(model, model_id, user_id, method):
    model_class = {
        'people': People,
        'planet': Planet,
        'vehicle': Vehicle
    }
    if model not in ['people', 'planet', 'vehicle']:
        return {'msg': f'No existe el modelo {model}'}, 404 
    
    user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one_or_none()
    if not user:
        return {'msg': f'No existe el usuario con id {user_id}'}, 404    
    
    new_favorite = db.session.execute(db.select(model_class.get(model)).filter_by(id=model_id)).scalar_one_or_none()
    if not new_favorite:
        return {'msg': f'No se encontro {model} con id {model_id}'}, 404
    
    find_favorite = db.session.execute(db.select(Favorite).filter_by(model=model, model_id=model_id, user_id=user_id)).scalar_one_or_none()
    if find_favorite and method == 'post':
        return {'msg': 'El usuario ya cuenta con el favorito solicitado'}, 400

    if method == 'post':
        favorite = {
            'user_id': user.serialize().get('id'),
            'model': model,
            'model_id': model_id
        }
        user_favorite = Favorite.add_favorite(favorite)

        return {'msg': 'favorito agregado correctamente'}, 201
    elif method == 'delete':
        if not find_favorite:
            return {'msg': 'No existe el favorito a eliminar'}, 400
        delete_favorite = Favorite.delete_favorite(find_favorite)
        return {'msg': 'Favorito eliminado'}, 202
    
    return {'msg': 'No se ha configurado un metodo adecuado para la solicitud'}, 400

@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/users', methods=['GET'])
def handle_users():
    msg, code = get_registers(User, 'users')
    return jsonify(msg), code

@app.route('/people', methods=['GET'])
def handle_people():
    msg, code = get_registers(People, 'people')
    return jsonify(msg), code

@app.route('/people/<people_id>')
def handle_search_people_by_id(people_id):
    msg, code = get_register_by_id(People, people_id, 'people')
    return jsonify(msg), code

@app.route('/planets', methods=['GET'])
def handle_planets():
    msg, code = get_registers(Planet, 'planets')
    return jsonify(msg), code

@app.route('/planets/<planet_id>', methods=['GET'])
def handle_search_planet_by_id(planet_id):
    msg, code = get_register_by_id(Planet, planet_id, 'planet')
    return jsonify(msg), code

@app.route('/vehicles', methods=['GET'])
def handle_vehicles():
    msg, code = get_registers(Vehicle, 'vehicles')
    return jsonify(msg), code

@app.route('/users/<user_id>/favorities', methods=['GET'])
def handle_search_favorities_by_user_id(user_id):
    if not user_id.isdigit():
        return jsonify({'msg': 'Debe indicar el id del usuario'}), 404
    user = int(user_id)
    user_favorities = db.session.execute(db.select(Favorite).filter_by(user_id=user)).scalars().all()
    favorities_list = [{'model': favorite.model, 'info':favorite.get_item().serialize()} for favorite in user_favorities]
    return jsonify({'favorities': favorities_list}), 200

@app.route('/favorite/<model>/<int:model_id>/<int:user_id>', methods=['POST'])
def handle_add_favorite_to_user(model, model_id, user_id):
    msg, code = validate_favorite(model, model_id, user_id, 'post')

    return jsonify(msg), code
    

@app.route('/favorite/<model>/<int:model_id>/<int:user_id>', methods=['DELETE'])
def handle_delete_favorite_to_user(model, model_id, user_id):
    msg, code = validate_favorite(model, model_id, user_id, 'delete')

    return jsonify(msg), code


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
