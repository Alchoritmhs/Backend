from Chains import chain_user_1, chain_user_2, FileBlockchain, signature2

# хардкод
doc_name = 'договор сантехника'
doc_version = '1'
document = 'договор.txt'

"""
функция создания файла инитит цепочку файла, и добавляет свой id подписанту на подпись
при этом владелец дока подписывает его 
"""
def create_document(doc_name, doc_version, owner, signer, document):
    owner_id = owner.last_block['id']
    owner_signature = owner.last_block['signature']
    owner_signature_ts = owner.last_block['timestamp']

    chain_file = FileBlockchain(doc_name=doc_name, doc_version=doc_version, owner_id=owner_id,
                                owner_signature=owner_signature, owner_signature_ts=owner_signature_ts,
                                signer=signer, document=document)

    signer.to_sign.append(chain_file.last_block['id'])

    return chain_file

"""
функция подписи файла подписантом берет подписанный с одной стороны файл, проверяет подпись 
и если все ок дописывает новый блок в цепочку файла, а также закрывает новый блок у владельца этого файла
"""
def sign_document_by_signer(file, owner, signer, signature):
    owner_id = owner.last_block['id']
    owner_signature = owner.last_block['signature']
    owner_signature_ts = owner.last_block['timestamp']

    signer_id = signer.last_block['id']
    signer_signature = signer.last_block['signature']
    signer_signature_ts = signer.last_block['timestamp']

    if signature:  # тут подтверждение подписи
        tmp_id = file.last_block['id']
        file.new_block(doc_name=doc_name, doc_version=doc_version, owner_id=owner_id,
                       owner_signature=owner_signature, owner_signature_ts=owner_signature_ts,
                       document=document, signer_id=signer_id, signer_signature=signer_signature,
                       signer_signature_ts=signer_signature_ts, previous_hash=FileBlockchain.hash(file.last_block))

        signer.to_sign.remove(tmp_id)
        owner.new_block(user_data=owner.last_block['user_data'], signer_id=signer_id,
                        signer_data=signer.last_block['user_data'], doc_id=file.last_block['id'],
                        doc_ver=file.last_block['version'], signer_signature=signature)
        return file


file1 = create_document(doc_name, doc_version, chain_user_1, chain_user_2, document)
file1 = sign_document_by_signer(file1, chain_user_1, chain_user_2, signature2)

print('владелец файла')
print(chain_user_1.__dict__)
print('подписант файла')
print(chain_user_2.__dict__)
print('файла')
print(file1.__dict__)
