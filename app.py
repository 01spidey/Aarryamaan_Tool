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


@app.route("/upload_or_update_product", methods=["POST", "UPDATE"])
def upload_or_update_product():
    """ Upload a product to the database """
    try:
        request_data = request.json

        product_name = request_data["name"].lower()
        product_category = request_data["category"].lower()
        product_description = request_data["description"]

        # the image must be sent as a base64 encoded string
        product_image = request_data["product_image"]
        model_image = request_data["model_image"]

        imagekit_folder_path = (
            f"/Aaaryamaan_Asset_Files/{product_category}/{product_name}"
        )

        products = mongo_instance.get_collection("aarryamaan", "products")

        if request.method == "POST":
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

            doc_id = f"{'_'.join(product_category.split(' '))}__{'_'.join(product_name.split(' '))}"
            mongo_obj = {
                "_id": doc_id,
                "name": product_name,
                "category": product_category,
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
        else:
            mongo_id = request_data["mongo_id"]
            result = products.update_one(
                {"_id": mongo_id},
                {
                    "$set": {
                        "name": product_name,
                        "category": product_category,
                        "description": product_description,
                    }
                },
            )

            mongo_doc = products.find_one({"_id": mongo_id})

            if product_image:
                product_image_id = mongo_doc["product_image"]["fileId"]
                product_image_upload_response = imagekit_api.update_image(
                    file_id=product_image_id,
                    file=product_image,
                    file_name=f"{product_category}__{product_name}_product.jpg",
                    folder_path=imagekit_folder_path,
                )

                products.update_one(
                    {"_id": mongo_id},
                    {"$set": {"product_image": product_image_upload_response}},
                )

            if model_image:
                model_image_id = mongo_doc["model_image"]["fileId"]
                model_image_upload_response = imagekit_api.update_image(
                    file_id=model_image_id,
                    file=model_image,
                    file_name=f"{product_category}__{product_name}_model.jpg",
                    folder_path=imagekit_folder_path,
                )

                products.update_one(
                    {"_id": mongo_id},
                    {"$set": {"model_image": model_image_upload_response}},
                )

            return jsonify(
                {
                    "success": True,
                    "message": "Product updated successfully",
                    "modified_count": result.modified_count,
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
