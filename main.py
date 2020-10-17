from Chains import UserBlockchain, FileBlockchain
from uuid import uuid4
import time
import hashlib
from flask import Flask, jsonify, request, make_response
from pymongo import MongoClient

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/uploads'
node_identifier = str(uuid4()).replace('-', '')

client = MongoClient('localhost', 27017)
mydatabase = client.blockchains
users = mydatabase.users
files = mydatabase.files


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
    users.insert_one(
        {'chain': blockchain.chain, 'login': login, 'to_sign': blockchain.to_sign, 'my_docs': blockchain.my_docs})
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
    db = {}
    for i in users.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'login':
                login = i[j]
        db.update({login: local})
    if login in db:
        password_db = db[login]['chain'][-1]['password']
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
    db = {}
    for i in users.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'login':
                login = i[j]
        db.update({login: local})
    if login in db:
        response = {
            'user_data': db[login]['chain'][-1]['user_data'],
            'files_ids_to_sign': db[login]['to_sign'],
            'my_files': db[login]['my_docs']
        }
        return jsonify(response), 200


@app.route('/upload', methods=['POST'])
def upload():
    file_name = request.values['file_name']
    file = eval(request.values['data'])
    str_file = ''
    for i in file:
        str_file += f'{i}: {file[i]}\n'
    cookies = request.cookies
    login = cookies['login']
    db_files = {}
    for i in files.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'id':
                f_id = i[j]
        db_files.update({f_id: local})
    db_users = {}
    for i in users.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'login':
                login = i[j]
        db_users.update({login: local})
    blockchain = FileBlockchain(doc_name=file_name, doc_version=0, owner_login=login, document=str_file)
    files.insert_one({'chain': blockchain.chain, 'id': blockchain.last_block['id']})
    curr_to_sign = db_users[login]['to_sign']
    curr_to_sign.append(blockchain.last_block['id'])
    users.update_one({'login': login}, {'$set': {'to_sign': curr_to_sign}})
    response = {'status': 'OK', 'message': 'File uploaded'}
    return jsonify(response), 200


@app.route('/file_info', methods=['POST'])
def file_info():
    file_id = request.values['id']
    db_files = {}
    for i in files.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'id':
                f_id = i[j]
        db_files.update({f_id: local})
    if file_id in db_files:
        file = db_files[file_id]['chain'][-1]
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

    db_files = {}
    for i in files.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'id':
                f_id = i[j]
        db_files.update({f_id: local})
    db_users = {}
    for i in users.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'login':
                login = i[j]
        db_users.update({login: local})

    chain = db_users[login]['chain']

    curr_to_sign = db_users[login]['to_sign']
    curr_to_sign.remove(id_to_sign)
    users.update_one({'login': login}, {'$set': {'to_sign': curr_to_sign}})
    curr_my_doc = db_users[login]['to_sign']
    curr_my_doc.append(id_to_sign)
    users.update_one({'login': login}, {'$set': {'my_docs': curr_my_doc}})
    db_users[login]['my_docs'].append(id_to_sign)
    db_users[login]['to_sign'].remove(id_to_sign)
    my_docs = db_users[login]['my_docs']
    to_sign = db_users[login]['to_sign']
    doc_ver = db_files[id_to_sign]['chain'][-1]['version']

    new_block_user = UserBlockchain.new_block(chain=chain, my_docs=my_docs, to_sign=to_sign, doc_ver=doc_ver,
                                              doc_id=id_to_sign)

    prev_chain = db_users[login]['chain']
    prev_chain.append(new_block_user)
    users.update_one({'login': login}, {'$set': {'chain': prev_chain}})

    chain = db_files[id_to_sign]['chain']
    doc_version = db_files[id_to_sign]['chain'][-1]['version']
    doc_name = db_files[id_to_sign]['chain'][-1]['name']
    owner_signature = db_users[login]['chain'][-1]['signature']

    new_block_file = FileBlockchain.new_block(chain=chain, doc_version=doc_version, doc_name=doc_name,
                                              owner_signature=owner_signature, owner_login=login,
                                              owner_signature_ts=db_users[login]['chain'][-1]['timestamp'])
    prev_chain = db_files[id_to_sign]['chain']
    prev_chain.append(new_block_file)
    files.update_one({'id': id_to_sign}, {'$set': {'chain': prev_chain}})

    response = {'status': 'OK', 'message': 'File signed'}
    return jsonify(response), 200


@app.route('/send_doc_to_sign', methods=['POST'])
def send_to_sign():
    cookies = request.cookies
    login = cookies['login']
    signer_login = request.values['signer_login']
    id_to_sign = request.values['id']
    db_users = {}
    for i in users.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'login':
                logini = i[j]
        db_users.update({logini: local})
    owner_file_ids = db_users[login]['my_docs']
    if id_to_sign in owner_file_ids:
        curr_to_sign = db_users[signer_login]['to_sign']
        curr_to_sign.append(id_to_sign)
        users.update_one({'login': signer_login}, {'$set': {'to_sign': curr_to_sign}})
        response = {'status': 'OK', 'message': f'File sent to user {signer_login}'}
        return jsonify(response), 200


@app.route('/sing_smbds_doc', methods=['POST'])
def sing_smbds_doc():
    cookies = request.cookies
    signer_login = cookies['login']
    file_id = request.values['id']
    db_files = {}
    for i in files.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'id':
                f_id = i[j]
        db_files.update({f_id: local})
    db_users = {}
    for i in users.find({}, {'_id': False}):
        local = {}
        for j in i:
            local.update({j: i[j]})
            if j == 'login':
                logini = i[j]
        db_users.update({logini: local})
    files_to_sign = db_users[signer_login]['to_sign']
    if file_id in files_to_sign:
        owner_login = db_files[file_id]['chain'][-1]['owner_login']
        chain = db_users[owner_login]['chain']
        my_docs = db_users[owner_login]['my_docs']
        to_sign = db_users[owner_login]['to_sign']
        doc_ver = db_files[file_id]['chain'][-1]['version']

        curr_to_sign = db_users[signer_login]['to_sign']
        curr_to_sign.remove(file_id)
        users.update_one({'login': signer_login}, {'$set': {'to_sign': curr_to_sign}})

        new_block_user = UserBlockchain.new_block(chain=chain,
                                                  my_docs=my_docs,
                                                  to_sign=to_sign,
                                                  doc_ver=doc_ver,
                                                  doc_id=file_id,
                                                  signer_signature=db_users[signer_login]['chain'][-1]['signature'],
                                                  signer_login=signer_login,
                                                  signer_data=db_users[signer_login]['chain'][-1]['user_data']
                                                  )
        db_users[owner_login]['chain'].append(new_block_user)
        prev_chain = db_users[owner_login]['chain']
        prev_chain.append(new_block_user)
        users.update_one({'login': owner_login}, {'$set': {'chain': prev_chain}})

        chain = db_files[file_id]['chain']
        doc_version = db_files[file_id]['chain'][-1]['version']
        doc_name = db_files[file_id]['chain'][-1]['name']
        owner_signature = db_users[owner_login]['chain'][-1]['signature']
        new_block_file = FileBlockchain.new_block(chain=chain, doc_version=doc_version, doc_name=doc_name,
                                                  owner_signature=owner_signature, owner_login=owner_login,
                                                  signer_login=signer_login,
                                                  signer_signature=db_users[signer_login]['chain'][-1]['signature'],
                                                  owner_signature_ts=db_users[signer_login]['chain'][-1][
                                                      'timestamp'],
                                                  signer_signature_ts=db_users[owner_login]['chain'][-1]['timestamp']
                                                  )

        db_files[file_id]['chain'].append(new_block_file)
        prev_chain = db_files[file_id]['chain']
        prev_chain.append(new_block_file)
        files.update_one({'id': file_id}, {'$set': {'chain': prev_chain}})
        response = {'status': 'OK', 'message': 'File signed'}
        return jsonify(response), 200


@app.route('/', methods=['GET'])
def test():
    response = {'status': 'OK', 'message': 'Work'}
    return jsonify(response), 200


if __name__ == '__main__':
    # users.delete_many({})
    # files.delete_many({})

    app.run(host='127.0.0.1', port=5000)
