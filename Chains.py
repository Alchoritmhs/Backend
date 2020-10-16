import hashlib
import json
import time


# класс цепочки для файла, пока в ините каша, для хардкода, далее красивее сделаю
class FileBlockchain:
    def __init__(self, doc_name, doc_version, owner_id, owner_signature, owner_signature_ts, signer, document):
        self.chain = []

        # Создание блока генезиса
        self.generic_block(doc_name=doc_name, doc_version=doc_version, owner_id=owner_id,
                           owner_signature=owner_signature, owner_signature_ts=owner_signature_ts,
                           signer=signer, document=document)



    # отказался от генерика тут, тк логичнее,
    # что файл адекватнее созадвать с первым блоком,
    # тк отдельно от юзеров он существовать не может, пока писал создание дока передумал
    def generic_block(self, doc_name, doc_version, owner_id, owner_signature,
                      owner_signature_ts, signer, document):
        block = {
            'index': len(self.chain) + 1,  # номер в цепочка
            'timestamp': time.time(),
            'version': doc_version,
            'name': doc_name,
            'owner_id': owner_id,
            'owner_signature': owner_signature,
            'owner_signature_ts': owner_signature_ts,
            'signer_id': signer_id,
            'document': document,
            'id': FileBlockchain.hash(document),
            'previous_hash': FileBlockchain.hash(document)  # сам себе хэш для генерик блока
        }
        self.chain.append(block)
        return block

    # добавление блока
    def new_block(self, doc_name, doc_version, owner_id, signer_id, owner_signature, signer_signature,
                      owner_signature_ts, signer_signature_ts, document, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,  # номер в цепочка
            'timestamp': time.time(),
            'version': doc_version,
            'name': doc_name,
            'owner_id': owner_id,
            'signer_id': signer_id,
            'owner_signature': owner_signature,
            'signer_signature': signer_signature,
            'owner_signature_ts': owner_signature_ts,
            'signer_signature_ts': signer_signature_ts,
            'document': document,
            'id': FileBlockchain.hash(document),
            'previous_hash': FileBlockchain.hash(previous_hash)  # сам себе хэш для генерик блока
        }
        self.chain.append(block)
        return block

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


class UserBlockchain:
    def __init__(self, user_data, signature):
        self.chain = []

        # список файлов на подпись ПОКА НЕ ПРИДУМАЛ, ЧТО С ЭТИМ ДЕЛАТЬ
        self.to_sign = []
        # Создание блока генезиса
        self.generic_block(user_data=user_data, signature=signature)

    def generic_block(self, user_data, signature):
        block = {
            'index': len(self.chain) + 1,  # номер в цепочка, да я дебил начинаю с 1, хз как с 1 начать, при логике, что индекс некст блока это длина цепочки + 1
            'timestamp': time.time(),  # тс
            'signature': signature,  # подпись
            'user_data': user_data,
            'id': UserBlockchain.hash(user_data),
            'previous_hash': UserBlockchain.hash(user_data),  # предыдущий хэш
        }
        self.chain.append(block)
        return block

    # добавление блока
    def new_block(self, user_data, signer_id, signer_data, doc_id, doc_ver, signer_signature,
                  previous_hash=None):
        block = {
            'index': len(self.chain) + 1,  # номер в цепочка
            'timestamp': time.time(),  # тс
            'signature': self.last_block['signature'],  # подпись
            'signer_signature': signer_signature,
            'user_data': user_data,
            'doc_id': doc_id,
            'doc_ver': doc_ver,
            'signer_id': signer_id,
            'signer_data': signer_data,
            'previous_hash': UserBlockchain.hash(previous_hash),  # предыдущий хэш
        }

        self.chain.append(block)
        return block

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


u_data1 = {
    'name': 'Pavel',
    'surname': 'Razuvaev'
}
signature1 = '12345'

u_data2 = {
    'name': 'Oleg',
    'surname': 'Popov'
}

signature2 = '67890'
chain_user_1 = UserBlockchain(user_data=u_data1, signature=signature1)
chain_user_2 = UserBlockchain(user_data=u_data2, signature=signature2)

doc_name = 'договор сантехники'
doc_version = '1'
owner_id = chain_user_1.last_block['id']
signer_id = chain_user_2.last_block['id']
owner_signature = chain_user_1.last_block['signature']
signer_signature = chain_user_2.last_block['signature']
owner_signature_ts = chain_user_1.last_block['timestamp']
signer_signature_ts = chain_user_2.last_block['timestamp']
document = 'договор.txt'


