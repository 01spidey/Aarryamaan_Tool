from imagekit_helper import ImageKitAPI
from dotenv import load_dotenv
import os
from imagekitio import ImageKit

load_dotenv()

imagekit_api = None

IMAGEKIT_BASE_PATH = "Aarryamaan_Website_Images/Products_Page/iloveimg-resized"


def get_imagekit_instance():
    global imagekit_api

    if imagekit_api:
        return imagekit_api
    else:
        print(os.getenv("IMAGEKIT_PUBLIC_KEY"))
        imagekit_api = ImageKitAPI(
            public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
            private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
            url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT"),
        )
        return imagekit_api


def upload_imagekit_instance():
    return ImageKit(
        private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
        public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
        url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT"),
    )
