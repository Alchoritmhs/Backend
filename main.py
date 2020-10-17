from Chains import UserBlockchain, FileBlockchain, create_document, sign_document_by_signer
from helpers import inin_pkl, readFile, rewriteFile
from uuid import uuid4
import os
import time
import hashlib
from flask import Flask, jsonify, request, make_response


def magic(signature_1, signature_2):  # тут, как я понял должна быть распознавашка
    return '***'


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/uploads'
node_identifier = str(uuid4()).replace('-', '')
def get_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()


@app.route('/register', methods=['POST'])
def register():
    """
        user_data - любой json {'name': '', 'surname': '', ...}
        signature - строчка подписи

    :return:
    """
    values = request.values
    login = values['login']
    password = get_hash(values['password'])
    signature = get_hash(f"{values['signature']}{time.time()}")
    user_data = eval(values['user_data'])
    blockchain = UserBlockchain(user_data=user_data, signature=signature, login=login, password=password)
    db = readFile('data/db.pkl')
    db['users'].update({login: blockchain.__dict__})
    rewriteFile('data/db.pkl', db)
    response = {'status': 'OK', 'message': 'User registered', }
    return jsonify(response), 200


@app.route('/login', methods=['POST'])
def login():
    """
        user_id - любой json {'name': '', 'surname': '', ...}
        signature - строчка подписи

        :return:
    """
    values = request.values
    login = values['login']
    password = get_hash(values['password'])
    db = readFile('data/db.pkl')
    if login in db['users']:
        password_db = db['users'][login]['chain'][-1]['password']
        if password_db == password:
            response = make_response()
            response.set_cookie('login', login)
            response.url = '127.0.0.1:5000/account'
    return response, 302


@app.route('/account', methods=['GET'])
def account():
    """
        ничего не принимает, нужна только кука чтобы дать список доков на подпись и данные юзера

        :return:
    """
    cookies = request.cookies
    login = cookies['login']
    db = readFile('data/db.pkl')
    if login in db['users']:
        response = {
            'user_data': db['users'][login]['chain'][-1]['user_data'],
            'files_ids_to_sign': db['users'][login]['chain'][-1]['to_sign'],
            'my_files': db['users'][login]['chain'][-1]['my_docs']
        }
        return jsonify(response), 200


if __name__ == '__main__':
    # инитим огурчики, решил так ибо нет времени разбираться с редисом/монгой или подобными(
    inin_pkl()
    db = readFile('data/db.pkl')
    doc_name = 'договор сантехника'
    doc_version = '1'
    document = 'договор.txt'
    app.run(host='127.0.0.1', port=5000)

# file1 = create_document(doc_name, doc_version, chain_user_1, chain_user_2, document)
# file1 = sign_document_by_signer(file1, chain_user_1, chain_user_2, signature2)
#
# print('владелец файла')
# print(chain_user_1.__dict__)
# print('подписант файла')
# print(chain_user_2.__dict__)
# print('файла')
# print(file1.__dict__)
