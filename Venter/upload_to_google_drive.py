"""
Author: Shivam Sharma

This file is use to upload the output and the Difference files to the google drive of venteriitb@gmail.com

The documentation can be found here => https://developers.google.com/drive/api/v3/manage-uploads
Video tutorial link => https://youtu.be/-7YH6rdR-tk
Stack OverFlow question => https://stackoverflow.com/questions/48436959/how-to-upload-csv-file-and-use-it-from-google-drive-into-google-colaboratory
"""
from __future__ import print_function
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from httplib2 import Http


def upload_to_drive(path_folder, filename, filename_diff, path_file, path_file_diff):
    from oauth2client import file, client, tools

    # First we need to give authentication for our drive to strore the files in it
    scopes = 'https://www.googleapis.com/auth/drive.appfolder https://www.googleapis.com/auth/drive.file'
    # credentials.json stores the credentials of the drive and the authentication keys. Once authenticated it doesn't ask again
    store = file.Storage('credentials.json')
    credentials = store.get()

    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', scope=scopes)
        credentials = tools.run_flow(flow, store)

    # Providing the version of the drive. Here we have used v3 which was the latest at the point of this development
    drive = discovery.build('drive', 'v3', http=credentials.authorize(Http()))

    # Initializing the output folder in the drive
    folder_metadata = {
        'name': path_folder,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = drive.files().create(body=folder_metadata,
                                fields='id').execute()

    folder_id = file.get('id')
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }

    # Initializing the difference folder in the drive
    diff_metadata = {
        'name': filename_diff,
        'parents': [folder_id]
    }

    # Uploading the result file
    media = MediaFileUpload(path_file,
                            mimetype=None,
                            resumable=False)

    # Uploading the difference file
    media_diff = MediaFileUpload(path_file_diff,
                                 mimetype=None,
                                 resumable=False)

    drive.files().create(body=file_metadata,
                         media_body=media,
                         fields='id').execute()

    drive.files().create(body=diff_metadata,
                         media_body=media_diff,
                         fields='id').execute()
