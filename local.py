import threading
import os
import logging
import time
import signal
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
import sys


logging.basicConfig(level=logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stdout_handler.setFormatter(formatter)
logging.getLogger().addHandler(stdout_handler)

# Set the values for your Azure AD App registration
TENANT_ID = os.environ.get('TENANT_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def run():
    try:
        # Create a credential object using the service principal
        credential = ClientSecretCredential(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )

        # Create a BlobServiceClient object using the Blob storage account URL and the credential
        blob_service_client = BlobServiceClient(account_url="https://demo01devwestorage.blob.core.windows.net", credential=credential)

        # Get a BlobClient object for the text file you want to read
        blob_client = blob_service_client.get_blob_client(container="democontainer", blob="demofile.txt")

        # Download the contents of the text file as bytes
        blob_data = blob_client.download_blob().readall()

        # Decode the bytes to a string
        text_data = blob_data.decode()

    except Exception as ex:
        logging.error(f"error: {ex}")

    while True:
        # print(text_data)
        logging.info(text_data)
        time.sleep(5)


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


# main function
def main():
    # create a Daemon tread
    t = threading.Thread(daemon=True, target=run, name="worker")
    t.start()

    killer = GracefulKiller()
    while not killer.kill_now:
        time.sleep(1)

    logging.info("Doing some important cleanup before exiting")
    logging.info("Gracefully exiting")


if __name__ == "__main__":
    main()
