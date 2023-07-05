from flask_restful import Resource, reqparse
from sqlalchemy.sql.functions import user

from models.usuario import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt, get_jwt
import bcrypt # Usei essa biblioteca como solução contraria do curso visando que a versão do curso não suporta novas versões do python
from blacklist import BLACKLIST

# from werkzeug.security import safe_str_cmp

atributos = reqparse.RequestParser()
atributos.add_argument('login', type=str, required=True, help="This  filed 'login' cannot be left too")
atributos.add_argument('senha', type=str, required=True, help="This  filed 'senha' cannot be left too")
atributos.add_argument('ativado', type=bool)

class User(Resource):
    # /usuarios/{user_id}

    def get(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            return user.json()
        return {'message': 'User not found.'}, 404 # not found

    @jwt_required()
    def delete(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            user.delete_user()
            return {'message': 'User deleted.'}
        return {'message': 'User not found.'}, 404

class UserRegister(Resource):
    # /cadastro
    def post(self):
        dados = atributos.parse_args()

        if UserModel.find_by_login(dados['login']):
            return {"message": "The login '{}' already exists.".format(dados['login'])}

        hashed_password = bcrypt.hashpw(dados['senha'].encode('utf-8'), bcrypt.gensalt())
        dados['senha'] = hashed_password.decode('utf-8')

        user = UserModel(**dados)
        user.ativado = False
        user.save_user()
        return {'message': 'User created successfully!'}, 201


class UserLogin(Resource):
    @classmethod
    def post(cls):
        dados = atributos.parse_args()

        user = UserModel.find_by_login(dados['login'])

        if user and bcrypt.checkpw(dados['senha'].encode('utf-8'), user.senha.encode('utf-8')):
            if user.ativado:
                token_de_acesso = create_access_token(identity=user.user_id)
                return {'access_token': token_de_acesso}, 200
            return {'massage': 'User not confirmed.'}, 400
        return {'message': 'The username or password is incorrect.'}, 401

class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jwt_id = get_jwt()['jti']  # JWT Token Identifier
        BLACKLIST.add(jwt_id)
        return {'message': 'Logged out successfully!'}, 200

class UserConfirm(Resource):
    # /raiz_do_site/confirmacao/{user_id}
    @classmethod
    def get(cls, user_id):
        user = UserModel.find_user(user_id)

        if not user:
            return {"message": "User id '{}' not found.".format(user_id)}, 404

        user.ativado = True
        user.save_user()
        return {"message": "User id '{}' confirmed successfully.".format(user_id)}, 200
