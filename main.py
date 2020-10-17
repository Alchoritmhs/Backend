from Chains import UserBlockchain, FileBlockchain, create_document, sign_document_by_signer
from helpers import inin_pkl, readFile, rewriteFile
from uuid import uuid4
import os
from flask import Flask, jsonify, request, make_response


def magic(signature_1, signature_2):  # тут, как я понял должна быть распознавашка
    return '***'


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/uploads'
node_identifier = str(uuid4()).replace('-', '')


@app.route('/register', methods=['POST'])
def register():
    """
        user_data - любой json {'name': '', 'surname': '', ...}
        signature - строчка подписи

    :return:
    """
    values = request.values
    blockchain = UserBlockchain(user_data=eval(values['user_data']), signature=values['signature'])
    user_id = blockchain.last_block['id']
    db = readFile('data/db.pkl')
    db['users'].update({user_id: blockchain})
    rewriteFile('data/db.pkl', db)
    response = {'status': f'OK\nUser registered {user_id}'}
    return jsonify(response), 200


@app.route('/login', methods=['POST'])
def login():
    """
        user_id - любой json {'name': '', 'surname': '', ...}
        signature - строчка подписи

        :return:
    """
    values = request.values
    user_id = values['user_id']
    signarure = values['signature']
    db = readFile('data/db.pkl')
    if user_id in db['users']:
        if signarure == db['users'][user_id].last_block['signature']:
            response = make_response()
            response.set_cookie('id', user_id)
            response.url = '127.0.0.1:5000/lk'
    return response, 302


@app.route('/account', methods=['GET'])
def account():
    """
        ничего не принимает, нужна только кука чтобы дать список доков на подпись и данные юзера

        :return:
    """
    cookies = request.cookies
    id_cookie = cookies['user_id']
    db = readFile('data/db.pkl')
    if id_cookie in db['users']:
        response = {
            'user_data': db['users'][id_cookie].last_block['user_data'],
            'files_ids_to_sign': db['users'][id_cookie].to_sign
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
