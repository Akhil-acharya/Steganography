from flask import Flask, render_template, request, send_file
from PIL import Image
import io

app = Flask(__name__)

def genData(data):
    return [format(ord(i), '08b') for i in data]

def modifyDataWithKey(data, key):
    key_bin = genData(key)
    key_len = len(key_bin)
    modified_data = []
    
    for i, byte in enumerate(data):
        key_byte = key_bin[i % key_len]
        modified_byte = ''.join(['1' if byte[j] != key_byte[j] else '0' for j in range(8)])
        modified_data.append(modified_byte)
    
    return modified_data

def reverseDataWithKey(modified_data, key):
    key_bin = genData(key)
    key_len = len(key_bin)
    original_data = []
    
    for i, byte in enumerate(modified_data):
        key_byte = key_bin[i % key_len]
        original_byte = ''.join(['1' if byte[j] != key_byte[j] else '0' for j in range(8)])
        original_data.append(original_byte)
    
    return original_data

def modPix(pix, data):
    lendata = len(data)
    imdata = iter(pix)

    for i in range(lendata):
        pix_values = [value for value in next(imdata)[:3] +
                      next(imdata)[:3] +
                      next(imdata)[:3]]

        for j in range(8):
            if data[i][j] == '0' and pix_values[j] % 2 != 0:
                pix_values[j] -= 1
            elif data[i][j] == '1' and pix_values[j] % 2 == 0:
                if pix_values[j] != 0:
                    pix_values[j] -= 1
                else:
                    pix_values[j] += 1

        if i == lendata - 1:
            if pix_values[-1] % 2 == 0:
                if pix_values[-1] != 0:
                    pix_values[-1] -= 1
                else:
                    pix_values[-1] += 1
        else:
            if pix_values[-1] % 2 != 0:
                pix_values[-1] -= 1

        pix_values = tuple(pix_values)
        yield pix_values[0:3]
        yield pix_values[3:6]
        yield pix_values[6:9]

def encode_enc(newimg, data, key):
    w, h = newimg.size
    x, y = 0, 0

    data_bin = genData(data)
    modified_data = modifyDataWithKey(data_bin, key)
    
    for pixel in modPix(newimg.getdata(), modified_data):
        newimg.putpixel((x, y), pixel)
        x += 1
        if x == w:
            x = 0
            y += 1

def decode_data(image, key):
    data = ''
    imgdata = iter(image.getdata())

    while True:
        pixels = [value for value in next(imgdata)[:3] +
                  next(imgdata)[:3] +
                  next(imgdata)[:3]]

        binstr = ''.join('1' if i % 2 != 0 else '0' for i in pixels[:8])
        data += chr(int(binstr, 2))
        if pixels[-1] % 2 != 0:
            break

    modified_data = genData(data)
    original_data = reverseDataWithKey(modified_data, key)
    return ''.join(chr(int(byte, 2)) for byte in original_data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    image = request.files['image']
    data = request.form['data']
    key = request.form['key']
    
    if image and data and key:
        img = Image.open(image)
        newimg = img.copy()
        encode_enc(newimg, data, key)
        
        byte_io = io.BytesIO()
        newimg.save(byte_io, 'PNG')
        byte_io.seek(0)
        
        return send_file(byte_io, mimetype='image/png', as_attachment=True, download_name='encoded_image.png')

    return 'Missing data', 400

@app.route('/decode', methods=['POST'])
def decode():
    image = request.files['image']
    key = request.form['key']
    
    if image and key:
        img = Image.open(image)
        decoded_data = decode_data(img, key)
        return decoded_data

    return 'Missing data', 400

if __name__ == "__main__":
    app.run(debug=True)
