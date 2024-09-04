import threading
import queue
from flask import Flask, jsonify, request
from utils import (
    upload_description,
    update_description,
    update_name,
    get_file_path,
    get_content_from_url,
)
from CONSTANTS import get_imagekit_instance, IMAGEKIT_BASE_PATH, upload_imagekit_instance
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager,
)
from flask_cors import CORS
from Crypto.Cipher import AES
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json
from flask_caching import Cache
import os
from dotenv import load_dotenv
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from imagekitio import ImageKit


load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")

jwt = JWTManager(app)
CORS(app)  # Enable CORS for all routes

imagekit_api = get_imagekit_instance()

# Load the secret key from environment variables
SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY")

# Configure caching
app.config["CACHE_TYPE"] = "SimpleCache"  # or "RedisCache" for production
app.config["CACHE_DEFAULT_TIMEOUT"] = 30000  # cache timeout in seconds
cache = Cache(app)

# Queue to handle requests
request_queue = queue.Queue()
processing_lock = threading.Lock()


def decrypt_data(encrypted_data):
    enc = base64.b64decode(encrypted_data)
    derived_key = base64.b64decode(SECRET_KEY)
    iv = "1020304050607080"
    cipher = AES.new(derived_key, AES.MODE_CBC, iv.encode("utf-8"))
    decrypted_bytes = unpad(cipher.decrypt(enc), 16)
    decrypt_data = decrypted_bytes.decode("utf-8")
    return decrypt_data

def process_request(request_data, func):
    """Function to process a request from the queue"""
    with processing_lock:
        response = func(request_data)
    return response


@app.route("/")
def sample():
    return jsonify({"message": "Vanakkam Bro!"})

@app.route("/login", methods=["POST"])
def login():
    encrypted_email = request.json.get("email", None)
    encrypted_password = request.json.get("password", None)

    if encrypted_email is None or encrypted_password is None:
        return jsonify({"msg": "Invalid data"}), 400

    email = decrypt_data(encrypted_email)
    password = decrypt_data(encrypted_password)

    if email is None or password is None:
        return jsonify({"msg": "Decryption failed"}), 400

    if email != "aarryamaanwebsite@gmail.com" or password != "website@gmail":
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token)


@app.route("/upload_product", methods=["POST"])
def upload_product():
    """Upload a product to the database"""
    try:
        request_data = request.json
        product_category = request_data["category"]
        product_name = request_data["name"]
        product_description = request_data["description"]

        model_image = request_data["model_image"]
        product_image = request_data["product_image"]
        factory_images = request_data["factory_images"]

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)

        # upload description
        upload_description(folder_path, product_name, product_description)

        # upload product and model image
        imagekit_api.upload_file(product_image, f"item", f"{folder_path}/Item")
        imagekit_api.upload_file(model_image, f"model", f"{folder_path}/Model")

        # upload factory images
        for idx, factory_image in enumerate(factory_images):
            imagekit_api.upload_file(
                factory_image, f"factory_img", f"{folder_path}/Factory_Images"
            )

        # Invalidate cache for the get_products endpoint
        cache.delete_memoized(get_products)

        return jsonify({"message": "Product uploaded successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/upload_factory_image", methods=["POST"])
def upload_factory_image():
    """Upload factory image to the database"""
    try:
        imagekit_upload_instance = upload_imagekit_instance()
        # Extract form data
        request_data = request.json
        product_category = request_data["category"]
        product_subcategory = request_data["subCategory"]
        file_name = request_data["fileName"]
        factory_image_file = request_data["file"]


        if not factory_image_file:
            return jsonify({"error": "No file uploaded"}), 400


        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_subcategory) + "/Factory_Images"
        print(folder_path)

        result = imagekit_upload_instance.upload_file(
            file = factory_image_file,
            file_name = file_name,
            options = UploadFileRequestOptions(folder = folder_path)
        )

        # Invalidate cache for the get_products endpoint
        cache.clear()

        return jsonify(
            {
                "message": "Factory image uploaded successfully",
                "result": {
                    "url": result.response_metadata.raw["url"],
                    "fileId": result.response_metadata.raw["fileId"],
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_product_info", methods=["PUT"])
def update_product_info():
    """Update a product in the database"""
    try:
        request_data = request.json

        if "description" in request_data:
            product_description = request_data["description"]
            product_name = request_data["name"]
            product_category = request_data["category"]

            folder_path = f"{IMAGEKIT_BASE_PATH}/{product_category}/{product_name}"
            folder_path = folder_path.replace(" ", "_")

            update_description(folder_path, product_name, product_description)

        else:
            product_category = request_data["category"]
            old_product_name = request_data["old_name"]
            new_product_name = request_data["new_name"]

            folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category)

            update_name(folder_path, old_product_name, new_product_name)

        # Invalidate cache for the get_products endpoint
        cache.delete_memoized(get_products)

        return jsonify({"message": "Product updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_image", methods=["PUT"])
def update_image():
    """Update an image in the database"""
    try:
        request_data = request.json
        product_category = request_data["category"]
        product_name = request_data["name"]
        image_type = request_data["type"]
        image_data = request_data["data"]

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)
        imagekit_api.delete_folder(f"{folder_path}/{image_type}")
        result = imagekit_api.upload_file(
            image_data, image_type, f"{folder_path}/{image_type}"
        )

        # Invalidate cache for the get_products endpoint
        cache.delete_memoized(get_products)

        return jsonify(
            {
                "message": "Image updated successfully",
                "result": result.response_metadata.raw["url"],
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_product", methods=["DELETE"])
def delete_product():
    """Delete a product from the database"""
    try:
        request_data = request.args
        product_category = request_data["category"]
        product_name = request_data["name"]

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)

        imagekit_api.delete_folder(folder_path)
        
        # Invalidate cache for the get_products endpoint
        cache.delete_memoized(get_products)

        return jsonify({"message": "Product deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_image", methods=["DELETE"])
def delete_factory_image():
    """Delete a factory image from the database"""
    try:
        file_id = request.args.get('fileID')
        print(file_id)

        imagekit_api.delete_file(file_id)

        # Invalidate cache for the get_products endpoint
        cache.clear()

        return jsonify({"message": "Factory image deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_products", methods=["GET"])
@cache.cached(key_prefix=lambda: f"get_products_{request.args.get('category')}_{request.args.get('subcategory', 'all')}")
def get_products():
    """Get all products from the database"""
    # try:
    request_data = request.args
    product_category = request_data["category"]

    folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category)
    product_assets = imagekit_api.list_assets(folder_path, "folder")

    result = []
    idx = 1

    for product_asset in product_assets:
        print(f'Lising assets in {folder_path}/{product_asset["name"]}')
        product_name = product_asset["name"]

        # get description
        description_asset = imagekit_api.list_assets(
            f"{folder_path}/{product_name}/Description", "file"
        )
        description_url = description_asset[0]["url"]
        description_txt = get_content_from_url(description_url).text

        # get product image
        product_image_asset = imagekit_api.list_assets(
            f"{folder_path}/{product_name}/Item", "file"
        )
        product_image_url = product_image_asset[0]["url"]
        product_image_fileId = product_image_asset[0]["fileId"]

        # get model image
        model_image = imagekit_api.list_assets(
            f"{folder_path}/{product_name}/Model", "file"
        )
        model_image_url = model_image[0]["url"]
        model_image_fileId = model_image[0]["fileId"]

        # get factory images
        factory_images = imagekit_api.list_assets(
            f"{folder_path}/{product_name}/Factory_Images", "file"
        )
        factory_images_data = [
            {
                "url": factory_image["url"],
                "fileId": factory_image["fileId"],
            }
            for factory_image in factory_images
        ]

        # format product name and category
        product_name = product_name.replace("_", " ").title()
        product_category = product_category.title()

        result.append(
            {
                "name": product_name,
                "category": product_category,
                "description": description_txt,
                "product_image": {
                    "url": product_image_url,
                    "fileId": product_image_fileId,
                },
                "model_image": {
                    "url": model_image_url,
                    "fileId": model_image_fileId,
                },
                "factory_images": factory_images_data,
                "id": idx,
            }
        )

        idx += 1

    return jsonify(
        {
            "success": True,
            "message": "Products fetched successfully",
            "data": result,
        }
    )

    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

# Function to handle concurrent request processing
def request_handler():
    while True:
        request_data, func = request_queue.get()
        process_request(request_data, func)
        request_queue.task_done()

# Start the request handler thread
handler_thread = threading.Thread(target=request_handler)
handler_thread.daemon = True
handler_thread.start()


if __name__ == "__main__":
    app.run(debug=True)
