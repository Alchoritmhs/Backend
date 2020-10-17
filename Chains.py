import hashlib
import json
import time


# класс цепочки для файла, пока в ините каша, для хардкода, далее красивее сделаю
class FileBlockchain:
    def __init__(self, doc_name, doc_version, owner_login, document):
        self.chain = []

        # Создание блока генезиса
        self.generic_block(doc_name=doc_name, doc_version=doc_version, owner_login=owner_login, document=document)

    # отказался от генерика тут, тк логичнее,
    # что файл адекватнее созадвать с первым блоком,
    # тк отдельно от юзеров он существовать не может, пока писал создание дока передумал
    def generic_block(self, doc_name, doc_version, owner_login, document):
        block = {
            'index': len(self.chain) + 1,  # номер в цепочка
            'timestamp': time.time(),
            'version': doc_version,
            'name': doc_name,
            'owner_login': owner_login,
            'document': document,
            'id': FileBlockchain.hash(document),
            'previous_hash': FileBlockchain.hash(document)  # сам себе хэш для генерик блока
        }
        self.chain.append(block)
        return block

    # добавление блока
    @staticmethod
    def new_block(chain, doc_name, doc_version, owner_login, owner_signature, document=None, signer_login=None,
                  signer_signature=None, owner_signature_ts=None, signer_signature_ts=None):
        last_block = chain[-1]
        block = {
            'index': len(chain) + 1,  # номер в цепочка
            'timestamp': time.time(),
            'version': doc_version,
            'name': doc_name,
            'owner_login': owner_login,
            'signer_login': signer_login,
            'owner_signature': owner_signature,
            'signer_signature': signer_signature,
            'owner_signature_ts': owner_signature_ts,
            'signer_signature_ts': signer_signature_ts,
            'document': document,
            'previous_hash': FileBlockchain.hash(last_block)
        }
        return block

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


class UserBlockchain:
    def __init__(self, user_data, login, password, signature):
        self.chain = []

        # список файлов на подпись ПОКА НЕ ПРИДУМАЛ, ЧТО С ЭТИМ ДЕЛАТЬ
        self.to_sign = []
        self.my_docs = []
        # Создание блока генезиса
        self.generic_block(user_data=user_data, login=login, signature=signature, password=password)

    def generic_block(self, user_data, login, password, signature):
        block = {
            'index': len(self.chain) + 1,  # номер в цепочка
            'timestamp': time.time(),  # тс
            'signature': signature,  # подпись
            'user_data': user_data,
            'to_sign': str(self.to_sign),
            'my_docs': str(self.my_docs),
            'login': login,
            'password': password,
            'previous_hash': UserBlockchain.hash(user_data),  # предыдущий хэш
        }
        self.chain.append(block)
        return block

    # добавление блока
    @staticmethod
    def new_block(chain, to_sign, my_docs, doc_id, doc_ver,
                  signer_signature=None, signer_login=None, signer_data=None):
        last_block = chain[-1]
        block = {
            'index': len(chain) + 1,  # номер в цепочка
            'timestamp': time.time(),  # тс
            'signature': last_block['signature'],  # подпись
            'signer_signature': signer_signature,
            'user_data': last_block['user_data'],
            'doc_id': doc_id,
            'doc_ver': doc_ver,
            'signer_login': signer_login,
            'signer_data': signer_data,
            'to_sign': str(to_sign),
            'my_docs': str(my_docs),
            'login': last_block['login'],
            'password': last_block['password'],
            'previous_hash': UserBlockchain.hash(last_block),  # предыдущий хэш
        }
        return block

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()



