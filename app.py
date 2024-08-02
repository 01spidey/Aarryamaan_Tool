from flask import Flask, jsonify, request
from utils import (
    upload_description,
    update_description,
    update_name,
    get_file_path,
)
from CONSTANTS import get_imagekit_instance, IMAGEKIT_BASE_PATH

app = Flask(__name__)

imagekit_api = get_imagekit_instance()


@app.route("/")
def sample():
    return jsonify({"message": "Vanakkam Bro!"})


@app.route("/upload_product", methods=["POST"])
def upload_product():
    """Update a product in the database"""
    try:
        request_data = request.json
        product_category = request_data["category"].lower()
        product_name = request_data["name"].lower()
        product_description = request_data["description"]

        model_image = request_data["model_image"]
        product_image = request_data["product_image"]
        factory_images = request_data["factory_images"]

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)

        # upload description
        upload_description(folder_path, product_name, product_description)

        # upload product and model image
        imagekit_api.upload_image(product_image, f"item", f'{folder_path}/item')
        imagekit_api.upload_image(model_image, f"model", f'{folder_path}/model')

        # upload factory images
        for idx, factory_image in enumerate(factory_images):
            imagekit_api.upload_image(factory_image, f"factory_img_{idx}", f'{folder_path}/factory_images')

        return jsonify({"message": "Product uploaded successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_product_info", methods=["PUT"])
def update_product_info():
    """Update a product in the database"""
    try:
        request_data = request.json

        if "description" in request_data:
            product_description = request_data["description"]
            product_name = request_data["name"].lower()
            product_category = request_data["category"].lower()

            folder_path = f"{IMAGEKIT_BASE_PATH}/{product_category}/{product_name}"
            folder_path = folder_path.replace(" ", "_")

            update_description(folder_path, product_name, product_description)

        else:
            product_category = request_data["category"].lower()
            old_product_name = request_data["old_name"].lower()
            new_product_name = request_data["new_name"].lower()

            folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category)

            update_name(folder_path, old_product_name, new_product_name)

        return jsonify({"message": "Product updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/delete_product", methods=["DELETE"])
def delete_product():
    """Delete a product from the database"""
    try:
        request_data = request.args
        product_category = request_data["category"].lower()
        product_name = request_data["name"].lower()

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)

        imagekit_api.delete_folder(folder_path)

        return jsonify({"message": "Product deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @app.route("/get_products", methods=["GET"])
# def get_products():
#     """ Get all products from the database """
#     try:
#         request_data = request.args
#         product_category = request_data["category"].lower()

#         products = mongo_instance.get_collection("aarryamaan", "products")
#         result = products.find({"category": product_category}).sort("name")

#         return jsonify(
#             {
#                 "success": True,
#                 "message": "Products fetched successfully",
#                 "products": list(result),
#             }
#         )

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
