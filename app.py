import threading
import queue
from flask import Flask, jsonify, request
from utils import (
    upload_description,
    update_description,
    update_name,
    get_file_path,
    get_content_from_url,
    update_factory_images,
)
from CONSTANTS import (
    get_imagekit_instance,
    IMAGEKIT_BASE_PATH,
    upload_imagekit_instance,
)
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager,
    verify_jwt_in_request,
    get_jwt
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
from datetime import datetime, timedelta
from functools import wraps


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
app.config["CACHE_DEFAULT_TIMEOUT"] = 3000  # cache timeout in seconds
cache = Cache(app)

# Queue to handle requests
request_queue = queue.Queue()
processing_lock = threading.Lock()

# Function to generate access token for a user with the given email and expiry time
def generate_token(email):
    expires = timedelta(hours=12)
    access_token = create_access_token(identity=email, expires_delta=expires)
    return access_token


#Custom decorator to check for JWT in the request header
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check for JWT in the request header
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Check if the token has expired
            if datetime.fromtimestamp(claims['exp']) < datetime.utcnow():
                return jsonify({"msg": "Token has expired"}), 401
            
            # Get the identity (email) from the token
            current_user = get_jwt_identity()
            
            # Validate email format
            if not current_user.endswith("@gmail.com"):
                return jsonify({"msg": "Unauthorized: Invalid email format"}), 401
            
        except Exception as e:
            return jsonify({"msg": "Unauthorized", "error": str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated_function


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
    return jsonify({"message": "Message from the server"})


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

    # Generate access token for the user
    
    access_token = generate_token(email)
    return jsonify(access_token=access_token)


@app.route("/upload_product", methods=["POST"])
@token_required
def upload_product():
    """Upload a product to the database"""
    try:
        request_data = request.json

        product_category = request_data["category"].replace(" ", "_")
        product_name = request_data["name"].replace(" ", "_")
        product_description = request_data["description"]

        model_image = request_data["model_image"]["url"]
        product_image = request_data["product_image"]["url"]
        factory_images = [img["url"] for img in request_data["factory_images"]]

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


@app.route("/update_product", methods=["POST"])
@token_required
def update_product():
    # """Upload a product to the database"""
    try:
        request_data = request.json

        is_changed = False

        old_data = request_data["old_data"]
        new_data = request_data["new_data"]

        if old_data == new_data:
            return jsonify({"message": "No changes made"})

        product_category = old_data["category"].replace(" ", "_")

        old_product_name = old_data["name"].replace(" ", "_")
        old_product_description = old_data["description"]
        old_model_image = old_data["model_image"]["url"]
        old_product_image = old_data["product_image"]["url"]
        old_factory_images = old_data["factory_images"]

        new_product_name = new_data["name"].replace(" ", "_")
        new_product_description = new_data["description"]
        new_model_image = new_data["model_image"]["url"]
        new_product_image = new_data["product_image"]["url"]
        new_factory_images = new_data["factory_images"]

        factory_images_updated = False

        if old_product_name != new_product_name:
            # Update Factory Images beforehand if product name is changed
            update_factory_images(
                old_factory_images,
                new_factory_images,
                get_file_path(IMAGEKIT_BASE_PATH, product_category, old_product_name),
            )
            factory_images_updated = True

            folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category)
            update_name(folder_path, old_product_name, new_product_name)
            is_changed = True
            print("Product name updated")

        folder_path = get_file_path(
            IMAGEKIT_BASE_PATH, product_category, new_product_name
        )

        if old_product_description != new_product_description:
            update_description(folder_path, new_product_name, new_product_description)
            is_changed = True
            print("Product description updated")

        if old_model_image != new_model_image:
            imagekit_api.delete_folder(f"{folder_path}/Model")
            imagekit_api.upload_file(new_model_image, f"model", f"{folder_path}/Model")
            is_changed = True
            print("Model image updated")

        if old_product_image != new_product_image:
            imagekit_api.delete_folder(f"{folder_path}/Item")
            imagekit_api.upload_file(new_product_image, f"item", f"{folder_path}/Item")
            is_changed = True
            print("Product image updated")

        if not factory_images_updated:
            update_factory_images(old_factory_images, new_factory_images, folder_path)
            is_changed = True

        # Invalidate cache for the get_products endpoint
        if is_changed:
            print("\nSomething is changed!! Cache cleared\n")
            cache.clear()
            return jsonify({"message": "Product updated successfully"})

        return jsonify({"message": "No changes made"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_product", methods=["DELETE"])
@token_required
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


# @app.route("/delete_image", methods=["DELETE"])
# def delete_factory_image():
#     """Delete a factory image from the database"""
#     try:
#         file_id = request.args.get('fileID')
#         print(file_id)

#         imagekit_api.delete_file(file_id)

#         # Invalidate cache for the get_products endpoint
#         cache.clear()

#         return jsonify({"message": "Factory image deleted successfully"})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app.route("/get_products", methods=["GET"])
@token_required
@cache.cached(
    key_prefix=lambda: f"get_products_{request.args.get('category')}_{request.args.get('subcategory', 'all')}"
)
def get_products():
    # """Get all products from the database"""
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
    app.run(debug=True, host='0.0.0.0', port=8080)
