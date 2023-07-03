from flask import current_app, jsonify
from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from models.site import SiteModel
from resources.filtros import normalize_path_params, consulta_com_cidade, consulta_sem_cidade

from flask_jwt_extended import jwt_required
import sqlite3

# path /hoteis?cidade=Rio de janeiro&estrelas_min=4&diaria_max=400

path_params = reqparse.RequestParser()

path_params.add_argument('cidade', type=str)
path_params.add_argument('estrelas_min', type=float)
path_params.add_argument('estrelas_max', type=float)
path_params.add_argument('diaria_min', type=float)
path_params.add_argument('diaria_max', type=float)
path_params.add_argument('limit', type=float)
path_params.add_argument('offset', type=float)


class Hoteis(Resource):
    # @jwt_required()
    def get(self):
        connection = sqlite3.connect(current_app.config['SQLALCHEMY_DATABASE_URI'])
        cursor = connection.cursor()

        dados = path_params.parse_args()
        dados_validos = {chave: dados[chave] for chave in dados if dados[chave] is not None}
        parametros = normalize_path_params(**dados_validos)

        if not parametros.get('cidade'):
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_sem_cidade, tupla)
        else:
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_com_cidade, tupla)

        hoteis = []
        for linha in resultado:
            hoteis.append({
                'hotel_id': linha[0],
                'nome': linha[1],
                'estrelas': linha[2],
                'diaria': linha[3],
                'cidade': linha[4],
                'site_id': linha[5]
            })

        return jsonify({'hoteis': hoteis})


class Hotel(Resource):
    atributos = reqparse.RequestParser()
    atributos.add_argument('nome', type=str, required=True, help='Campo não pode ser nulo')
    atributos.add_argument('estrelas', type=float, required=True, help="Estrelas não pode ser nulo")
    atributos.add_argument('diaria')
    atributos.add_argument('cidade')
    atributos.add_argument('site_id', type=int, required=True, help='Campo site não pode ser nulo')

    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': 'Hotel not found.'}, 404

    @jwt_required()
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {'message': 'Hotel id "{}" already exists.'.format(hotel_id)}, 400

        dados = Hotel.atributos.parse_args()
        hotel = HotelModel(hotel_id, **dados)

        if not SiteModel.find_by_id(dados.get('site_id')):
            return {'message': 'The hotel must be associated with a valid site id.'}

        # Tratando erros
        try:
            hotel.save_hotel()
        except:
            return {'message': 'Internal server error while trying to save.'}, 500

        return hotel.json()

    @jwt_required()
    def put(self, hotel_id):
        dados = Hotel.atributos.parse_args()

        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        if hotel_encontrado:
            hotel_encontrado.update_hotel(**dados)
            hotel_encontrado.save_hotel()
            return hotel_encontrado.json(), 200

        hotel = HotelModel(hotel_id, **dados)

        try:
            hotel.save_hotel()
        except:
            return {'message': 'Internal server error while trying to save.'}, 500

        return hotel.json(), 201


class SiteModel:
    @classmethod
    def find_by_id(cls, site_id):
        connection = sqlite3.connect(current_app.config['SQLALCHEMY_DATABASE_URI'])
        cursor = connection.cursor()

        query = "SELECT * FROM sites WHERE id = ?"
        result = cursor.execute(query, (site_id,))
        row = result.fetchone()

        if row:
            site = {
                'id': row[0],
                'name': row[1]
                # Adicione os outros atributos do site conforme necessário
            }
            return site

        return None


    @jwt_required()
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'Internal server error while trying to delete.'}, 500

            return {'message': 'Hotel deleted.'}
        return {'message': 'Hotel not found'}, 404


