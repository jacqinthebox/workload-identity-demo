import threading
import logging
import time
import signal
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
import sys

logging.basicConfig(level=logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stdout_handler.setFormatter(formatter)
logging.getLogger().addHandler(stdout_handler)

# Set the values for your Azure Blob Storage account and container
ACCOUNT_URL = 'https://demo01devwestorage.blob.core.windows.net'
CONTAINER_NAME = 'democontainer'
BLOB_NAME = 'demofile.txt'


def run():
    try:
        # Create a credential object using Managed Identity
        credential = ManagedIdentityCredential()

        # Create a BlobServiceClient object using the Blob storage account URL and the credential
        blob_service_client = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential)

        # Get a BlobClient object for the text file you want to read
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)

        # Download the contents of the text file as bytes
        blob_data = blob_client.download_blob().readall()

        # Decode the bytes to a string
        text_data = blob_data.decode()

    except Exception as ex:
        logging.error(f"error: {ex}")

    while True:
        # Write the contents of the text file to the standard output using the logging module
        logging.info(text_data)
        time.sleep(2)


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
