# Save this as `app.py`

import streamlit as st
import os
from io import BytesIO
from PIL import Image
import tempfile
from n2 import encode, decode  # Assuming your code is saved as encode_decode_module.py

# Streamlit UI setup
st.title("Hybrid Encryption to GIF Converter")

# Sidebar for file upload
st.sidebar.header("Upload File")
uploaded_file = st.sidebar.file_uploader("Choose a file (image, audio, text)", type=["jpg", "png", "mp3", "txt"])

# Options for encryption
vigenere_key = st.sidebar.text_input("Vigenère Key (For Hybrid Encryption)", value="SECRET")

# Check for file upload
if uploaded_file is not None:
    st.sidebar.write("Uploaded file:", uploaded_file.name)
    file_type = uploaded_file.type.split('/')[0]

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        temp_file_path = tmp_file.name

    # Encrypt and convert to GIF
    st.write(f"Encrypting {uploaded_file.name} and converting to GIF...")
    
    # Encoding the file
    output_gif_name = f"{uploaded_file.name}.gif"
    try:
        # Run encoding
        gif_path = encode(temp_file_path, vigenere_key=vigenere_key)
        st.success("Encryption and GIF generation completed!")

        # Display the GIF in the Streamlit app
        st.image(gif_path)

        # Provide a download button for the generated GIF
        with open(gif_path, "rb") as gif_file:
            gif_bytes = gif_file.read()
            st.download_button(
                label="Download Encrypted GIF",
                data=gif_bytes,
                file_name=output_gif_name,
                mime="image/gif"
            )

    except Exception as e:
        st.error(f"An error occurred during encryption: {e}")

# Decrypt Section
st.header("Decrypt GIF")
uploaded_gif = st.file_uploader("Upload Encrypted GIF for Decryption", type=["gif"])

if uploaded_gif is not None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_gif.getvalue())
        gif_file_path = tmp_file.name

    try:
        st.write("Decrypting GIF...")
        decode(gif_file_path, vigenere_key=vigenere_key)
        st.success("Decryption completed!")

        # Display a link or name of recovered file
        recovered_files_path = "recovered_files"
        recovered_files = os.listdir(recovered_files_path)
        if recovered_files:
            st.write("Recovered Files:")
            for recovered_file in recovered_files:
                st.write(recovered_file)

    except Exception as e:
        st.error(f"An error occurred during decryption: {e}")

