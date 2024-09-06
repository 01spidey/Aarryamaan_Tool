from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from imagekitio.models.DeleteFolderRequestOptions import DeleteFolderRequestOptions
from imagekitio.models.MoveFolderRequestOptions import MoveFolderRequestOptions
from imagekitio.models.CreateFolderRequestOptions import CreateFolderRequestOptions
from imagekitio.models.ListAndSearchFileRequestOptions import (
    ListAndSearchFileRequestOptions,
)


class ImageKitAPI:

    def __init__(self, public_key, private_key, url_endpoint):
        self.imagekit_api = ImageKit(
            private_key=private_key, public_key=public_key, url_endpoint=url_endpoint
        )
        self.public_key = public_key
        self.private_key = private_key

    def upload_file(self, file, file_name, folder_path):
        response = self.imagekit_api.upload_file(
            file=file,
            file_name=file_name,
            options=UploadFileRequestOptions(folder=folder_path),
        )

        return response.response_metadata.raw

    def delete_file(self, file_id):
        response = self.imagekit_api.delete_file(file_id)
        return response.response_metadata.raw

    def delete_folder(self, folder_path):
        response = self.imagekit_api.delete_folder(
            options=DeleteFolderRequestOptions(folder_path=folder_path)
        )
        return response

    def update_image(self, file_id, file, file_name, folder_path):
        self.delete_file(file_id)
        return self.upload_file(file, file_name, folder_path)

    def move_folder(self, source_folder_path, destination_folder_path):
        return self.imagekit_api.move_folder(
            options=MoveFolderRequestOptions(
                source_folder_path=source_folder_path,
                destination_path=destination_folder_path,
            )
        )

    def create_folder(self, folder_name, parent_folder_path):
        return self.imagekit_api.create_folder(
            options=CreateFolderRequestOptions(
                folder_name=folder_name, parent_folder_path=parent_folder_path
            )
        )

    def list_assets(self, folder_path, asset_type):
        assets = self.imagekit_api.list_files(
            options=ListAndSearchFileRequestOptions(
                type=asset_type,
                path=folder_path,
            )
        ).response_metadata.raw
        return assets
