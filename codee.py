
from PIL import Image
import binascii
import imageio.v2 as imageio  # updated for the latest imageio version
import os
import sys
from shutil import rmtree

four_k = (3840, 2160)
HD = (1920, 1080)

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
	
def decode(src,binary_key):
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
    bits = binary_vigenere_decrypt(bits,binary_key)
    bits=polybius_cipher_binary_reverse(bits)
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
def polybius_cipher_binary(data):
    # Define Polybius cipher square for binary data
    polybius_square = {
        "00": "11", "01": "10", "10": "01", "11": "00"
    }
    
    # Initialize encrypted data string
    encrypted_data = ""
    
    # Loop through the binary data in pairs of 2 bits
    for i in range(0, len(data) - 1, 2):  # Process in steps of 2 (no padding)
        pair = ''.join(data[i:i+2])  # Convert the list to a string
        encrypted_data += polybius_square.get(pair, "")
    
    # Return the encrypted binary data
    return encrypted_data

def polybius_cipher_binary_reverse(encrypted_data):
    # Define the reverse Polybius cipher square for binary data
    reverse_polybius_square = {
        "00": "11", "01": "10", "10": "01", "11": "00"
    }
    
    # Initialize the decrypted data string
    decrypted_data = ""
    
    # Loop through the encrypted data in chunks of 2 bits
    for i in range(0, len(encrypted_data), 2):
        pair = ''.join(encrypted_data[i:i+2])  # Convert the list to a string
        decrypted_data += reverse_polybius_square.get(pair, "")
    
    # Return the decrypted binary data
    return decrypted_data

def binary_vigenere_encrypt(data, key):
    # Repeat the key to match the length of the data
    repeated_key = (key * (len(data) // len(key) + 1))[:len(data)]
    
    # Perform XOR between data and repeated key
    encrypted_data = ''.join(
        str(int(bit) ^ int(repeated_key[i])) for i, bit in enumerate(data)
    )   
    return encrypted_data

def binary_vigenere_decrypt(encrypted_data, key):
    # Repeat the key to match the length of the encrypted data
    repeated_key = (key * (len(encrypted_data) // len(key) + 1))[:len(encrypted_data)]
    
    # Perform XOR between encrypted data and repeated key
    decrypted_data = ''.join(
        str(int(bit) ^ int(repeated_key[i])) for i, bit in enumerate(encrypted_data)
    )
    
    return decrypted_data



def encode(src,key, res):
    bits = file_2_bits(src)
    bits = add_header(bits, os.path.basename(src))

    bits =  polybius_cipher_binary(bits)

    bits = binary_vigenere_encrypt(bits,key)

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

import os

def convert_all_bin_to_jpg(input_folder, output_folder="recovered"):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Loop through all files in the input folder
    for filename in os.listdir(input_folder):
        # Check if the file has a .bin extension
        if filename.endswith(".bin"):
            bin_file_path = os.path.join(input_folder, filename)

            # Read binary data from the .bin file
            with open(bin_file_path, 'rb') as bin_file:
                binary_data = bin_file.read()

            # Set output path for the .jpg file
            jpg_file_name = os.path.splitext(filename)[0] + ".jpg"
            jpg_file_path = os.path.join(output_folder, jpg_file_name)

            # Write the binary data to the new .jpg file
            with open(jpg_file_path, 'wb') as jpg_file:
                jpg_file.write(binary_data)

            print(f"Converted {bin_file_path} to {jpg_file_path}")

# Example usage

"""def main():
    #encode("data/test.mp3")
    #decode("test.mp3.gif")

    #encode("data/test.txt")
    #decode("test.txt.gif")
    
    #encode("data/test.jpg")
    decode("test.jpg.gif")
    input_folder = "recovered_files"
    convert_all_bin_to_jpg(input_folder)
if __name__ == "__main__":
    main()

"""