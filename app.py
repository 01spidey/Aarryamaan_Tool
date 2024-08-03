from flask import Flask, jsonify, request
from utils import (
    upload_description,
    update_description,
    update_name,
    get_file_path,
    get_content_from_url,
)
from CONSTANTS import get_imagekit_instance, IMAGEKIT_BASE_PATH

app = Flask(__name__)

imagekit_api = get_imagekit_instance()


@app.route("/")
def sample():
    return jsonify({"message": "Vanakkam Bro!"})


@app.route("/upload_product", methods=["POST"])
def upload_product():
    """Upload a product to the database"""
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
        imagekit_api.upload_file(product_image, f"item", f"{folder_path}/item")
        imagekit_api.upload_file(model_image, f"model", f"{folder_path}/model")

        # upload factory images
        for idx, factory_image in enumerate(factory_images):
            imagekit_api.upload_file(
                factory_image, f"factory_img", f"{folder_path}/factory_images"
            )

        return jsonify({"message": "Product uploaded successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload_factory_image", methods=["POST"])
def upload_factory_image():
    """Upload a factory image to the database"""
    try:
        request_data = request.json
        product_category = request_data["category"].lower()
        product_name = request_data["name"].lower()
        factory_image_data = request_data["data"]

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)

        result = imagekit_api.upload_file(
            factory_image_data, f"factory_img", f"{folder_path}/factory_images"
        )

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


@app.route("/update_image", methods=["PUT"])
def update_image():
    """Update an image in the database"""
    try:
        request_data = request.json
        product_category = request_data["category"].lower()
        product_name = request_data["name"].lower()
        image_type = request_data["type"].lower()
        image_data = request_data["data"]

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)
        imagekit_api.delete_folder(f"{folder_path}/{image_type}")
        result = imagekit_api.upload_file(
            image_data, image_type, f"{folder_path}/{image_type}"
        )

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
        product_category = request_data["category"].lower()
        product_name = request_data["name"].lower()

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category, product_name)

        imagekit_api.delete_folder(folder_path)

        return jsonify({"message": "Product deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_factory_image", methods=["DELETE"])
def delete_factory_image():
    """Delete a factory image from the database"""
    try:
        request_data = request.args
        file_id = request_data["file_id"]

        imagekit_api.delete_file(file_id)

        return jsonify({"message": "Factory image deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_products", methods=["GET"])
def get_products():
    """Get all products from the database"""
    try:
        request_data = request.args
        product_category = request_data["category"].lower()

        folder_path = get_file_path(IMAGEKIT_BASE_PATH, product_category)
        product_assets = imagekit_api.list_assets(folder_path, "folder")

        result = []

        for product_asset in product_assets:
            product_name = product_asset["name"]

            # get description
            description_asset = imagekit_api.list_assets(
                f"{folder_path}/{product_name}/description", "file"
            )
            description_url = description_asset[0]["url"]
            description_txt = get_content_from_url(description_url).text

            # get product image
            product_image_asset = imagekit_api.list_assets(
                f"{folder_path}/{product_name}/item", "file"
            )
            product_image_url = product_image_asset[0]["url"]
            product_image_fileId = product_image_asset[0]["fileId"]

            # get model image
            model_image = imagekit_api.list_assets(
                f"{folder_path}/{product_name}/model", "file"
            )
            model_image_url = model_image[0]["url"]
            model_image_fileId = model_image[0]["fileId"]

            # get factory images
            factory_images = imagekit_api.list_assets(
                f"{folder_path}/{product_name}/factory_images", "file"
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
                }
            )

        return jsonify(
            {
                "success": True,
                "message": "Products fetched successfully",
                "data": result,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
