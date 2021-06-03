#!/usr/bin/env python3
# coding: utf-8
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials
import argparse, sys

parser = argparse.ArgumentParser()

parser.add_argument(
    '-l', '--locale', required = True,
    help=('Which locale we are downloading an export file for.'))

args = parser.parse_args()

LOCALE = args.locale
BUCKET_NAME = "public-content-export-data"
DOWNLOAD_TARGET_FILE = "tmp/tsv_download.%s.tsv" % LOCALE

def get_blobs_with_prefix(bucket_name, prefix):
    """Lists all the blobs in the bucket that begin with the prefix.
    Taken from sample code in docs:
    https://cloud.google.com/storage/docs/listing-objects#storage-list-objects-python

    This can be used to list all blobs in a "folder", e.g. "public/".
    """

    #storage_client = storage.Client()
    storage_client = storage.Client.create_anonymous_client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(
        bucket_name, prefix=prefix
    )

    result = []
    for blob in blobs:
        result.append(blob.name)

    return result

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket.

    Taken from sample code in docs:
    https://cloud.google.com/storage/docs/downloading-objects#storage-download-object-python
    """
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client.create_anonymous_client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Blob {} downloaded to {}".format(
            source_blob_name, destination_file_name
        )
    )

prefix = "%s-export" % LOCALE
blobs = get_blobs_with_prefix(BUCKET_NAME, prefix)

# Get the blob with the most recent timestamp
latest_blob = sorted(blobs, reverse=True)[0]
print("Downloading TSV for %s, version %s" % (LOCALE, latest_blob))

download_blob(BUCKET_NAME, latest_blob, DOWNLOAD_TARGET_FILE)
print("Downloaded blob to {}".format(DOWNLOAD_TARGET_FILE))
