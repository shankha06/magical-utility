#! python3
# backup_to_zip.py - Copies an entire folder and its contents into a zip file
# whose filename increments if it already exists.

import zipfile
import os


def backup_to_zip(folder):
    # Back up the entire contents of "folder" into a ZIP file.

    folder = os.path.abspath(folder)    # make sure folder is absolute

    # Figure out the filename this code should use based on what files already exist.
    number = 1

    # Name the backup file
    while True:
        zip_filename = os.path.basename(folder) + '_' + str(number) + '.zip'

        # Break if the file name does not exist. If it exists, it gives it name_(num + 1).zip and breaks
        if not os.path.exists(zip_filename):
            break
        number = number + 1

    # Create the Zip file
    print(f'Creating {zip_filename}...')

    backup_zip = zipfile.ZipFile(zip_filename, 'w')
    backup_zip.write(folder)

    # Walk the entire folder tree and compress the files in each folder.
    for foldername, subfolders, filenames in os.walk(folder):
        print(f'Adding files in {foldername}...')
        # Add the current folder to the ZIP file.
        backup_zip.write(foldername)

        # Add all the files in this folder to the ZIP file.
        for filename in filenames:
            new_base = os.path.basename(folder) + '_'
            if filename.startswith(new_base) and filename.endswith('.zip'):
                continue        # don't back up the backup ZIP files

            # Adding files
            backup_zip.write(os.path.join(foldername, filename))

    backup_zip.close()

    print('Done.')


# This failed to work with an absolute path
backup_to_zip('10_ORGANIZING_FILES')

# If os.walk() is not used, an empty zip file would be created.
