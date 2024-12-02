from __future__ import print_function
import string

from PIL import Image
import binascii
import imageio.v2 as imageio  # updated for the latest imageio version
import os
import sys
from shutil import rmtree

four_k = (3840, 2160)
HD = (1920, 1080)
res=four_k
# Polybius Square
polybius_square = {
    'A': '11', 'B': '12', 'C': '13', 'D': '14', 'E': '15',
    'F': '21', 'G': '22', 'H': '23', 'I': '24', 'J': '24', 'K': '25',
    'L': '31', 'M': '32', 'N': '33', 'O': '34', 'P': '35',
    'Q': '41', 'R': '42', 'S': '43', 'T': '44', 'U': '45',
    'V': '51', 'W': '52', 'X': '53', 'Y': '54', 'Z': '55'
}

inverse_polybius_square = {v: k for k, v in polybius_square.items()}

# Vigenère Cipher Functions
def vigenere_encrypt(text, key):
    encrypted = []
    key = key.upper()
    for i, char in enumerate(text):
        if char.isalpha():
            shift = ord(key[i % len(key)]) - ord('A')
            encrypted_char = chr(((ord(char) - ord('A') + shift) % 26) + ord('A'))
            encrypted.append(encrypted_char)
        else:
            encrypted.append(char)
    return ''.join(encrypted)

def vigenere_decrypt(text, key):
    decrypted = []
    key = key.upper()
    for i, char in enumerate(text):
        if char.isalpha():
            shift = ord(key[i % len(key)]) - ord('A')
            decrypted_char = chr(((ord(char) - ord('A') - shift + 26) % 26) + ord('A'))
            decrypted.append(decrypted_char)
        else:
            decrypted.append(char)
    return ''.join(decrypted)

# Polybius and Vigenère Hybrid Encryption
def hybrid_encrypt(plaintext, vigenere_key):
    # Step 1: Apply Polybius encryption
    polybius_encrypted = ''.join(polybius_square.get(char.upper(), '') for char in plaintext if char.upper() in polybius_square)
    
    # Step 2: Apply Vigenère cipher on the Polybius output
    vigenere_encrypted = vigenere_encrypt(polybius_encrypted, vigenere_key)
    return vigenere_encrypted

def hybrid_decrypt(encrypted_text, vigenere_key):
    # Step 1: Apply Vigenère decryption
    vigenere_decrypted = vigenere_decrypt(encrypted_text, vigenere_key)
    
    # Step 2: Convert Polybius numbers back to text
    polybius_decrypted = ''.join(inverse_polybius_square.get(vigenere_decrypted[i:i+2], '') for i in range(0, len(vigenere_decrypted), 2))
    return polybius_decrypted

# Modify the encode/decode functions to use the hybrid encryption/decryption
def encode(src,  vigenere_key="SECRET"):
    bits = file_2_bits(src)
    bits = add_header(bits, os.path.basename(src))
    
    # Encrypt bits using hybrid encryption (convert to string first)
    bit_string = ''.join(bits)
    encrypted_text = hybrid_encrypt(bit_string, vigenere_key)
    
    # Convert encrypted text back to bits and then to pixels
    encrypted_bits = list(encrypted_text)  # Convert encrypted text back to bits
    pixels = bits_2_pixels(encrypted_bits)
    pixels_per_image = res[0] * res[1]
    num_imgs = (len(pixels) + pixels_per_image - 1) // pixels_per_image
    
    clear_folder("temp")
    for i in range(num_imgs):
        cur_temp_name = f"temp/{os.path.basename(src)}-{i}.png"
        cur_start_idx = i * pixels_per_image
        cur_pixels = pixels[cur_start_idx:cur_start_idx + pixels_per_image]
        pixels_2_png(cur_pixels, cur_temp_name)
    
    return make_gif("temp", os.path.basename(src))

def decode(src, vigenere_key="SECRET"):
    # Decode steps (from your existing code)
    def iter_frames(im):
        try:
            i = 0
            while True:
                im.seek(i)
                yield im.convert("RGB")
                i += 1
        except EOFError:
            pass

    pixels = []
    with Image.open(src) as im:
        for frame in iter_frames(im):
            pixels.extend(list(frame.getdata()))
    
    bits = pixels_2_bits(pixels)
    fname, bits = decode_header(bits)
    
    # Decrypt bits using hybrid decryption (convert to string first)
    bit_string = ''.join(bits)
    decrypted_text = hybrid_decrypt(bit_string, vigenere_key)
    
    # Convert decrypted text back to original bits
    original_bits = list(decrypted_text)
    recovered_fname = f"recovered_files/{fname}-recovered.bin"
    
    os.makedirs("recovered_files", exist_ok=True)
    bits_2_file(original_bits, recovered_fname)


def make_gif(parent_folder, fname):
    items = os.listdir(parent_folder)
    png_filenames = [elem for elem in items if elem.endswith(".png")]

    sorted_png = sorted(
        png_filenames,
        key=lambda p: int(p.split("-")[1].split(".")[0])
    )

    with imageio.get_writer(f"{fname}.gif", mode="I", duration=0.1) as writer:
        for filename in sorted_png:
            image = imageio.imread(os.path.join(parent_folder, filename))
            writer.append_data(image)
    return f"{fname}.gif"

def pixels_2_png(pixels, fname, reso=four_k):
    img = Image.new("RGB", reso)
    img.putdata(pixels)
    img.save(fname)
    print(f"pixels_2_png: Saved {len(pixels)} pixels to {fname}")

def png_2_pixels(fname):
    with Image.open(fname) as im:
        pixel_list = list(im.getdata())
    print(f"png_2_pixels: Read {len(pixel_list)} pixels from {fname}")
    return pixel_list

def bits_2_file(bits, fname):
    with open(fname, "wb") as f:
        for idx in range(0, len(bits), 8):
            byte = bits[idx:idx + 8]
            f.write(int("".join(byte), 2).to_bytes(1, "big"))

def file_2_bits(fname):
    bits = []
    with open(fname, "rb") as f:
        byte = f.read(1)
        while byte:
            bits.extend(bin(ord(byte))[2:].zfill(8))
            byte = f.read(1)
    return bits

def bits_2_pixels(bits):
    pixels = [(0, 0, 0) if b == "0" else (255, 255, 255) for b in bits]
    print(f"bits_2_pixels: Converted {len(bits)} bits to {len(pixels)} pixels")
    return pixels

def pixels_2_bits(pixels):
    bits = ["0" if p == (0, 0, 0) else "1" for p in pixels]
    print(f"pixels_2_bits: Converted {len(pixels)} pixels to {len(bits)} bits")
    return bits

def add_header(bits, fname):
    fname_bitstr = bin(int(binascii.hexlify(fname.encode()), 16))[2:]
    fname_bitstr_length_bitstr = bin(len(fname_bitstr))[2:].zfill(16)
    payload_length_header = bin(len(bits))[2:].zfill(64)
    header_list = list(fname_bitstr_length_bitstr + fname_bitstr + payload_length_header)
    return header_list + bits


import re

def decode_header(bits):
    def decode_binary_string(s):
        try:
            return ''.join(chr(int(s[i * 8:i * 8 + 8], 2)) for i in range(len(s) // 8))
        except ValueError:
            return None

    fname_length = int(''.join(bits[:16]), 2)
    fname_bits = ''.join(bits[16:16 + fname_length])
    payload_length = int(''.join(bits[16 + fname_length:16 + fname_length + 64]), 2)

    # Decode the file name and handle decoding errors
    fname = decode_binary_string(fname_bits)
    if not fname:
        fname = "default_name"
    
    # Sanitize the filename by keeping only alphanumeric characters, underscores, and dots
    fname = re.sub(r'[^A-Za-z0-9_.]', '_', fname)

    return fname, bits[16 + fname_length + 64:16 + fname_length + 64 + payload_length]
	
'''def decode(src):
    def iter_frames(im):
        try:
            i = 0
            while True:
                im.seek(i)
                yield im.convert("RGB")
                i += 1
        except EOFError:
            pass

    pixels = []
    with Image.open(src) as im:
        for frame in iter_frames(im):
            pixels.extend(list(frame.getdata()))
    
    bits = pixels_2_bits(pixels)
    fname, bits = decode_header(bits)

    # Ensure the recovered file name has its original extension (or defaults to .bin)
    if '.' in fname:
        recovered_fname = f"recovered_files/{fname.split('.')[0]}-recovered.{fname.split('.')[-1]}"
    else:
        recovered_fname = f"recovered_files/{fname}-recovered.bin"  # Default to .bin if no extension

    # Ensure the folder exists before saving
    os.makedirs("recovered_files", exist_ok=True)

    # Save the recovered file in its original format
    bits_2_file(bits, recovered_fname)


'''
def test_bit_similarity(bits1, bits2):
    if len(bits1) != len(bits2):
        print("Bit lengths are not the same!")
        return
    for b1, b2 in zip(bits1, bits2):
        if b1 != b2:
            print("Bits are not the same!")
            return
    print("Bits are identical")

def clear_folder(relative_path):
    try:
        rmtree(relative_path)
    except FileNotFoundError:
        print("WARNING: Could not locate /temp directory.")
    os.makedirs(relative_path, exist_ok=True)
'''
def encode(src, res=four_k):
    bits = file_2_bits(src)
    bits = add_header(bits, os.path.basename(src))
    pixels = bits_2_pixels(bits)
    pixels_per_image = res[0] * res[1]
    num_imgs = (len(pixels) + pixels_per_image - 1) // pixels_per_image
    clear_folder("temp")
    for i in range(num_imgs):
        cur_temp_name = f"temp/{os.path.basename(src)}-{i}.png"
        cur_start_idx = i * pixels_per_image
        cur_pixels = pixels[cur_start_idx:cur_start_idx + pixels_per_image]
        pixels_2_png(cur_pixels, cur_temp_name)
    return make_gif("temp", os.path.basename(src))

'''
def conversion_test():
    src_f = "data/test.jpg"
    img_f = "data/image.png"
    test_f_bits = add_header(file_2_bits(src_f), os.path.basename(src_f))
    pixels = bits_2_pixels(test_f_bits)
    pixels_2_png(pixels, img_f)
    pixels = png_2_pixels(img_f)
    bits = pixels_2_bits(pixels)
    fname, bits = decode_header(bits)
    bits_2_file(bits, f"{src_f.split('.')[0]}-copy.{src_f.split('.')[1]}")
    test_bit_similarity(file_2_bits(src_f), bits)

def main():
    #encode("data/test.mp3",'SECRET')
    #decode("test.mp3.gif",'SECRET')

    #encode("data/test.txt")
    #decode("test.txt.gif")

    encode("data/test.jpg",'SECRET')
    decode("test.jpg.gif",'SECRET')
if __name__ == "__main__":
    main()

