import random

ID_BITS = 32

def get_id_from_hex(hex_str):
    if not hex_str:
        return random.getrandbits(ID_BITS)
    return int(hex_str, 16)

def xor_distance(id1, id2):
    return id1 ^ id2

def get_bucket_index(distance):
    if distance == 0:
        return -1
    return distance.bit_length() - 1