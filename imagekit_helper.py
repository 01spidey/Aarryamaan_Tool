from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from imagekitio.models.DeleteFolderRequestOptions import DeleteFolderRequestOptions


class ImageKitAPI:
    base_path = "/Aaaryamaan_Asset_Files/"

    def __init__(self, public_key, private_key, url_endpoint):
        self.imagekit_api = ImageKit(
            private_key=private_key, public_key=public_key, url_endpoint=url_endpoint
        )

    def upload_image(self, file, file_name, folder_path):
        response = self.imagekit_api.upload_file(
            file=file,
            file_name=file_name,
            options=UploadFileRequestOptions(folder=folder_path),
        )

        return response.response_metadata.raw

    def delete_image(self, file_id):
        response = self.imagekit_api.delete_file(file_id)
        return response.response_metadata.raw

    def delete_folder(self, folder_path):
        response = self.imagekit_api.delete_folder(
            options=DeleteFolderRequestOptions(folder_path=folder_path)
        )
        return response
    
    def update_image(self, file_id, file, file_name, folder_path):
        self.delete_image(file_id)
        return self.upload_image(file, file_name, folder_path)
