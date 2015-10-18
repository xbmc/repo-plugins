import hashlib
import json
# from Crypto.Cipher import AES
import decrypter


def evpKDF(passwd, salt, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5"):
    target_key_size = key_size + iv_size
    derived_bytes = ""
    number_of_derived_words = 0
    block = None
    hasher = hashlib.new(hash_algorithm)
    while number_of_derived_words < target_key_size:
        if block is not None:
            hasher.update(block)

        hasher.update(passwd)
        hasher.update(salt)
        block = hasher.digest()
        hasher = hashlib.new(hash_algorithm)

        for i in range(1, iterations):
            hasher.update(block)
            block = hasher.digest()
            hasher = hashlib.new(hash_algorithm)

        derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]

        number_of_derived_words += len(block)/4

    return {
        "key": derived_bytes[0: key_size * 4],
        "iv": derived_bytes[key_size * 4:]
    }


def decrypt_url(dailytoday, subject):
    subject_json = json.loads(subject)
    data = evpKDF(dailytoday, subject_json['s'].decode('hex'))
    # aes = AES.new(data['key'], AES.MODE_CBC, data['iv'], segment_size=128)
    aes = decrypter.AESDecrypter().new(data['key'], decrypter.MODE_CBC, data['iv'])
    decrypted_data = aes.decrypt(subject_json['ct'].decode('base64'))
    pad = decrypted_data[-1]
    # pad_size = ord(decrypted_data[-1])
    return decrypted_data.rstrip(pad)[1:-1].replace('\\', '')
