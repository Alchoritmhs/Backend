from Chains import UserBlockchain, FileBlockchain
from helpers import inin_pkl, readFile, rewriteFile
from uuid import uuid4
import time
import hashlib
from flask import Flask, jsonify, request, make_response
from pymongo import MongoClient

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/uploads'
node_identifier = str(uuid4()).replace('-', '')

client = MongoClient('mongodb', 27017)
users = client.users
chains = client.chains
"""
добавление
users.insert_one({"name":"bob", "secondname":"smith"})
удаление
users.delete_one({"name":"bob"})
изменение
users.find_one_and_update({"name": "bob"}, {"$set": {"name":"Tom"}})
"""


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
            'files_ids_to_sign': db['users'][login]['to_sign'],
            'my_files': db['users'][login]['my_docs']
        }
        return jsonify(response), 200


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    cookies = request.cookies
    login = cookies['login']
    db = readFile('data/db.pkl')
    if bool(file.filename):
        file_bytes = file.read()
        blockchain = FileBlockchain(doc_name=file.filename, doc_version=0, owner_login=login, document=str(file_bytes))
        db['files'].update({blockchain.last_block['id']: blockchain.__dict__})
        db['users'][login]['to_sign'].append(blockchain.last_block['id'])
        rewriteFile('data/db.pkl', db)
        response = {'status': 'OK', 'message': 'File uploaded'}
        return jsonify(response), 200
    else:
        response = {'status': 'BAD', 'message': '', }
        return jsonify(response), 400


@app.route('/file_info', methods=['GET'])
def file_info():
    file_id = request.values['id']
    db = readFile('data/db.pkl')
    files = db['files']
    if file_id in files:
        file = db['files'][file_id]['chain'][-1]
        if 'owner_signature' in file:
            del file['owner_signature']
        if 'signer_signature' in file:
            del file['signer_signature']
        if 'index' in file:
            del file['index']
        if 'previous_hash' in file:
            del file['previous_hash']
        response = {'status': 'OK', 'message': file}
        return jsonify(response), 200


@app.route('/sign_doc_own', methods=['POST'])
def sign_file_own():
    cookies = request.cookies
    login = cookies['login']
    id_to_sign = request.values['id']

    db = readFile('data/db.pkl')
    chain = db['users'][login]['chain']
    db['users'][login]['my_docs'].append(id_to_sign)
    db['users'][login]['to_sign'].remove(id_to_sign)
    my_docs = db['users'][login]['my_docs']
    to_sign = db['users'][login]['to_sign']
    doc_ver = db['files'][id_to_sign]['chain'][-1]['version']

    new_block_user = UserBlockchain.new_block(chain=chain, my_docs=my_docs, to_sign=to_sign, doc_ver=doc_ver,
                                              doc_id=id_to_sign)
    db['users'][login]['chain'].append(new_block_user)

    chain = db['files'][id_to_sign]['chain']
    doc_version = db['files'][id_to_sign]['chain'][-1]['version']
    doc_name = db['files'][id_to_sign]['chain'][-1]['name']
    owner_signature = db['users'][login]['chain'][-1]['signature']

    new_block_file = FileBlockchain.new_block(chain=chain, doc_version=doc_version, doc_name=doc_name,
                                              owner_signature=owner_signature, owner_login=login,
                                              owner_signature_ts=db['users'][login]['chain'][-1]['timestamp'])
    db['files'][id_to_sign]['chain'].append(new_block_file)
    rewriteFile('data/db.pkl', db)

    response = {'status': 'OK', 'message': 'File signed'}
    return jsonify(response), 200


@app.route('/send_doc_to_sign', methods=['POST'])
def send_to_sign():
    cookies = request.cookies
    login = cookies['login']
    signer_login = request.values['signer_login']
    id_to_sign = request.values['id']
    db = readFile('data/db.pkl')
    owner_file_ids = db['users'][login]['my_docs']
    if id_to_sign in owner_file_ids:
        db['users'][signer_login]['to_sign'].append(id_to_sign)
        rewriteFile('data/db.pkl', db)
        response = {'status': 'OK', 'message': f'File sent to user {signer_login}'}
        return jsonify(response), 200


@app.route('/sing_smbds_doc', methods=['POST'])
def sing_smbds_doc():
    cookies = request.cookies
    signer_login = cookies['login']
    file_id = request.values['id']
    db = readFile('data/db.pkl')
    files_to_sign = db['users'][signer_login]['to_sign']
    if file_id in files_to_sign:
        owner_login = db['files'][file_id]['chain'][-1]['owner_login']
        chain = db['users'][owner_login]['chain']
        db['users'][signer_login]['to_sign'].remove(file_id)
        my_docs = db['users'][owner_login]['my_docs']
        to_sign = db['users'][owner_login]['to_sign']
        doc_ver = db['files'][file_id]['chain'][-1]['version']
        doc_ver = db['files'][file_id]['chain'][-1]['version']

        new_block_user = UserBlockchain.new_block(chain=chain,
                                                  my_docs=my_docs,
                                                  to_sign=to_sign,
                                                  doc_ver=doc_ver,
                                                  doc_id=file_id,
                                                  signer_signature=db['users'][signer_login]['chain'][-1]['signature'],
                                                  signer_login=signer_login,
                                                  signer_data=db['users'][signer_login]['chain'][-1]['user_data']
                                                  )
        db['users'][owner_login]['chain'].append(new_block_user)

        chain = db['files'][file_id]['chain']
        doc_version = db['files'][file_id]['chain'][-1]['version']
        doc_name = db['files'][file_id]['chain'][-1]['name']
        owner_signature = db['users'][owner_login]['chain'][-1]['signature']
        new_block_file = FileBlockchain.new_block(chain=chain, doc_version=doc_version, doc_name=doc_name,
                                                  owner_signature=owner_signature, owner_login=owner_login,
                                                  signer_login=signer_login,
                                                  signer_signature=db['users'][signer_login]['chain'][-1]['signature'],
                                                  owner_signature_ts=db['users'][signer_login]['chain'][-1][
                                                      'timestamp'],
                                                  signer_signature_ts=db['users'][owner_login]['chain'][-1]['timestamp']
                                                  )

        db['files'][file_id]['chain'].append(new_block_file)
        rewriteFile('data/db.pkl', db)
        response = {'status': 'OK', 'message': 'File signed'}
        return jsonify(response), 200


if __name__ == '__main__':
    # инитим огурчики, решил так ибо нет времени разбираться с редисом/монгой или подобными(
    inin_pkl()
    db = readFile('data/db.pkl')

    app.run(host='127.0.0.1', port=5000)
