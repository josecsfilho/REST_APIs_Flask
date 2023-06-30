from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required, get_jwt_identity

class Hoteis(Resource):
    def get(self):
        return {'hoteis': [hotel.json() for hotel in HotelModel.query.all()]} # SELECT * FROM hoteis

class Hotel(Resource):
    atributos = reqparse.RequestParser()
    atributos.add_argument('nome', type=str, required=True, help="The field 'nome' cannot be left bing.")
    atributos.add_argument('estrelas')
    atributos.add_argument('diaria')
    atributos.add_argument('cidade')

    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': 'Hotel not found.'}, 404 # not found

    @jwt_required()
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {'message': "Hotel id '{}' already exists.".format(hotel_id)}, 400 # Bad Request

        dados = Hotel.atributos.parse_args()
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'An internal error ocurred trying to save hotel.'}, 500
        return hotel.json(), 201

    @jwt_required()
    def put(self, hotel_id):
        dados = Hotel.atributos.parse_args()
        hotel = HotelModel(hotel_id, **dados)

        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        if hotel_encontrado:
            hotel_encontrado.update_hotel(**dados)
            hotel_encontrado.save_hotel()
            return hotel_encontrado.json(), 200
        hotel.save_hotel()
        return hotel.json(), 201  # criado
        # hotel = HotelModel(hotel_id, **dados)
        # try:
        #     hotel.save_hotel()
        # except:
        #     return {'message': 'An internal error ocurred trying to save hotel.'}, 500
        # return hotel.json(), 201 # criado

    @jwt_required()
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'An internal error ocurred trying to save hotel.'}, 500
            return  {'message': 'Hotel deleted.'}
        return {'message': 'Hotel not found.'}, 404