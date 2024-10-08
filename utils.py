import base64
import io
import os

import requests
from CONSTANTS import get_imagekit_instance

imagekit_api = get_imagekit_instance()


def upload_description(folder_path, product_name, description):
    folder_path = f"{folder_path}/Description"
    product_name = product_name.replace(" ", "_")

    txt_data = convert_to_txt(description)

    response = imagekit_api.upload_file(
        file=txt_data,
        file_name=f"description.txt",
        folder_path=folder_path,
    )

    return response


def update_description(folder_path, product_name, description):
    imagekit_api.delete_folder(f"{folder_path}/Description")
    upload_description(folder_path, product_name, description)


def update_name(folder_path, old_name, new_name):

    imagekit_api.create_folder(new_name, folder_path)
    internal_folder_paths = ["Factory_Images", "Item", "Model", "Description"]
    for internal_folder_path in internal_folder_paths:
        old_folder_path = get_file_path(folder_path, old_name, internal_folder_path)
        new_folder_path = get_file_path(folder_path, new_name)

        imagekit_api.create_folder(internal_folder_path, new_folder_path)
        imagekit_api.move_folder(old_folder_path, new_folder_path)

    imagekit_api.delete_folder(get_file_path(folder_path, old_name))


def convert_to_txt(string):
    file_obj = io.StringIO(string)
    file_content = file_obj.read()
    file_content_bytes = file_content.encode("utf-8")

    # return as base64 encoded string
    return base64.b64encode(file_content_bytes).decode("utf-8")


def get_file_path(base_path, *args):
    file_path = os.path.join(base_path, *args)
    return file_path


def get_content_from_url(url):
    response = requests.get(url)
    return response


def process_name(name):
    return name.replace(" ", "_")


def update_factory_images(old_factory_images, new_factory_images, folder_path):
    old_factory_img_fileIDs = [img["fileId"] for img in old_factory_images]
    new_factory_img_fileIDs = [img["fileId"] for img in new_factory_images]

    for factory_image in new_factory_images:

        if factory_image["fileId"] not in old_factory_img_fileIDs:
            imagekit_api.upload_file(
                factory_image["url"], f"factory_img", f"{folder_path}/Factory_Images"
            )
            print("Factory image uploaded")

    for factory_image in old_factory_images:
        if factory_image["fileId"] not in new_factory_img_fileIDs:
            imagekit_api.delete_file(factory_image["fileId"])
            print("Factory image deleted")
