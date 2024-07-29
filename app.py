from flask import Flask, jsonify, request
from pymongo import MongoClient
from imagekit_helper import ImageKitAPI
from mongo_helper import MongoHelper
from dotenv import load_dotenv
import os

load_dotenv()


app = Flask(__name__)

mongo_instance = MongoHelper(
    username=os.getenv("MONGO_USERNAME"),
    password=os.getenv("MONGO_PASSWORD"),
)

imagekit_api = ImageKitAPI(
    public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT"),
)

@app.route("/")
def sample():
    return jsonify({"message": "Vanakkam Bro!"})


@app.route("/upload_product", methods=["POST"])
def upload_product():
    """ Upload a product to the database """
    try:
        request_data = request.json
        product_category = request_data["category"].lower()
        product_name = request_data["name"].lower()
        product_description = request_data["description"]

        # the image must be sent as a base64 encoded string
        product_image = request_data["product_image"]
        model_image = request_data["model_image"]

        imagekit_folder_path = (
            f"/Aaaryamaan_Asset_Files/{product_category}/{product_name}"
        )

        product_image_upload_response = imagekit_api.upload_image(
            file=product_image,
            file_name=f"{product_category}__{product_name}_product.jpg",
            folder_path=imagekit_folder_path,
        )

        model_image_upload_response = imagekit_api.upload_image(
            file=model_image,
            file_name=f"{product_category}__{product_name}_model.jpg",
            folder_path=imagekit_folder_path,
        )

        products = mongo_instance.get_collection("aarryamaan", "products")
        doc_id = f"{'_'.join(product_category.split(' '))}__{'_'.join(product_name.split(' '))}"
        mongo_obj = {
            "_id": doc_id,
            "category": product_category,
            "name": product_name,
            "description": product_description,
            "product_image": product_image_upload_response,
            "model_image": model_image_upload_response,
        }

        result = products.insert_one(mongo_obj)

        return jsonify(
            {
                "success": True,
                "message": "Product uploaded successfully",
                "product_id": str(result.inserted_id),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e.__traceback__)}), 500


@app.route("/get_products", methods=["GET"])
def get_products():
    """ Get all products from the database """
    try:
        request_data = request.args
        product_category = request_data["category"].lower()

        products = mongo_instance.get_collection("aarryamaan", "products")
        result = products.find({"category": product_category}).sort("name")

        return jsonify(
            {
                "success": True,
                "message": "Products fetched successfully",
                "products": list(result),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_product", methods=["DELETE"])
def delete_product():
    """ Delete a product from the database """
    try:
        request_data = request.json
        mongo_id = request_data["mongo_id"]
        imagekit_folder_path = request_data["imagekit_folder_path"]

        imagekit_api.delete_folder(imagekit_folder_path)

        products = mongo_instance.get_collection("aarryamaan", "products")
        result = products.delete_one({"_id": mongo_id})

        return jsonify(
            {
                "success": True,
                "message": "Product deleted successfully",
                "deleted_count": result.deleted_count,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_product", methods=["PUT"])
def update_product():
    try:
        """ Update a product in the database """
        request_data = request.json
        mongo_id = request_data["mongo_id"]
        product_category = request_data["category"].lower()
        product_name = request_data["name"].lower()
        product_description = request_data["description"]

        """
            Yet to implement the image update functionality
        """

        return jsonify({"message": "Product updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
