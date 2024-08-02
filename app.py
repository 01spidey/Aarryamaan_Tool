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
        imagekit_api.upload_image(product_image, f"item", f"{folder_path}/item")
        imagekit_api.upload_image(model_image, f"model", f"{folder_path}/model")

        # upload factory images
        for idx, factory_image in enumerate(factory_images):
            imagekit_api.upload_image(
                factory_image, f"factory_img_{idx}", f"{folder_path}/factory_images"
            )

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

            # get model image
            model_image = imagekit_api.list_assets(
                f"{folder_path}/{product_name}/model", "file"
            )
            model_image_url = model_image[0]["url"]

            # get factory images
            factory_images = imagekit_api.list_assets(
                f"{folder_path}/{product_name}/factory_images", "file"
            )
            factory_image_urls = [
                factory_image["url"] for factory_image in factory_images
            ]

            # format product name and category
            product_name = product_name.replace("_", " ").title()
            product_category = product_category.title()

            result.append(
                {
                    "name": product_name,
                    "category": product_category,
                    "description": description_txt,
                    "product_image": product_image_url,
                    "model_image": model_image_url,
                    "factory_images": factory_image_urls,
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
