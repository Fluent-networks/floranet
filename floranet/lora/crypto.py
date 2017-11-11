from CryptoPlus.Cipher import python_AES

def aesEncrypt(key, data, mode=None):
    """AES encryption function
    
    Args:
        key (str): packed 128 bit key
        data (str): packed plain text data
        mode (str): Optional mode specification (CMAC)
        
    Returns:
        Packed encrypted data string
    """
    if mode == 'CMAC':
        # Create AES cipher using key argument, and encrypt data
        cipher = python_AES.new(key, python_AES.MODE_CMAC)
    elif mode == None:
        cipher = python_AES.new(key)
    return cipher.encrypt(data)

def aesDecrypt(key, data):
    """AES decryption fucnction
    
    Args:
        key (str): packed 128 bit key
        data (str): packed encrypted data
        
    Returns:
        Packed decrypted data string
    """
    cipher = python_AES.new(key)
    return cipher.decrypt(data)

