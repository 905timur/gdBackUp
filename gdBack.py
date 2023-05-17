import os
import logging
import tkinter as tk
from tkinter import filedialog, scrolledtext
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tkinter import ttk
from datetime import datetime
import threading


def authenticate(credentials_file):
    try:
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile(credentials_file)
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth)
        return drive
    except Exception as e:
        logging.error(f"Authentication failed: {str(e)}")
        raise


def create_folder(drive, folder_name, parent_id=None):
    try:
        query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        existing_folders = drive.ListFile({'q': query}).GetList()
        if existing_folders:
            return existing_folders[0]

        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        if parent_id:
            folder_metadata['parents'] = [{'id': parent_id}]
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        return folder
    except Exception as e:
        logging.error(f"Failed to create folder: {str(e)}")
        raise


def upload_file(drive, folder_id, file_path):
    try:
        gfile = drive.CreateFile({'parents': [{'id': folder_id}]})
        gfile.SetContentFile(file_path)
        gfile.Upload()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"{timestamp} - Uploaded: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to upload file: {str(e)}")
        return False


def upload_folder(drive, folder_path, parent_id=None):
    try:
        folder_name = os.path.basename(folder_path)
        folder_id = None

        query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        existing_folders = drive.ListFile({'q': query}).GetList()
        if existing_folders:
            folder_id = existing_folders[0]['id']

        if folder_id is None:
            if parent_id is None:
                folder = create_folder(drive, "Automated Backup Folder")
            else:
                folder = create_folder(drive, folder_name, parent_id)
            folder_id = folder['id']

        total_files = sum(len(files) for _, _, files in os.walk(folder_path))
        count = 0

        query = f"'{folder_id}' in parents and trashed=false"
        existing_files = drive.ListFile({'q': query}).GetList()
        existing_file_names = {file['title']: file['modifiedDate'] for file in existing_files}

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)

                if file in existing_file_names:
                    local_modified_time = os.path.getmtime(file_path)
                    drive_modified_time = datetime.strptime(existing_file_names[file][:19], "%Y-%m-%dT%H:%M:%S")
                    if drive_modified_time >= datetime.fromtimestamp(local_modified_time):
                        count += 1
                        continue

                if upload_file(drive, folder_id, file_path):
                    count += 1

        logging.info("-" * 30)
        logging.info("")
        logging.info("Folder backup completed.")
        return True
    except Exception as e:
        logging.error(f"Folder backup failed: {str(e)}")
        return False


def add_folder():
    folder_path = filedialog.askdirectory(mustexist=True)
    if folder_path:
        folder_entry = tk.Entry(folders_frame, width=40)
        folder_entry.insert(tk.END, folder_path)
        folder_entry.pack()
        folder_entries.append(folder_entry)


def backup_folders():
    folder_paths = [entry.get() for entry in folder_entries]
    invalid_folders = []

    credentials_file = 'XXX.json'  # Insert your JSON credentials file here
    drive = authenticate(credentials_file)
    if not drive:
        status_label.config(text="Authentication failed.")
        return

    automated_backup_folder = create_folder(drive, "Automated Backup Folder")

    for folder_path in folder_paths:
        if os.path.isdir(folder_path):
            threading.Thread(target=upload_folder, args=(drive, folder_path, automated_backup_folder['id'])).start()
        else:
            invalid_folders.append(folder_path)

    if len(invalid_folders) == 0:
        status_label.config(text="Backup started.")
    else:
        invalid_folder_paths = "\n".join(invalid_folders)
        status_label.config(text=f"Invalid folder paths:\n{invalid_folder_paths}")


# Main window
window = tk.Tk()
window.title("Folder Backup")
window.geometry("600x400")

# Folders frame
folders_frame = ttk.Frame(window)
folders_frame.pack()

# GUI elements
folder_label = tk.Label(folders_frame, text="Select Folders to Backup:")
folder_label.pack()

folder_entries = []  # List to store folder entry fields

add_folder_button = tk.Button(folders_frame, text="Add Folder", command=add_folder)
add_folder_button.pack()

backup_button = tk.Button(window, text="Backup", command=backup_folders)
backup_button.pack()

status_label = tk.Label(window, text="")
status_label.pack()

# Progress bar
progress_bar = ttk.Progressbar(window, orient='horizontal', length=500, mode='determinate')
progress_bar.pack()

# Event Log
event_log_frame = ttk.Frame(window)
event_log_frame.pack(fill=tk.BOTH, expand=True)

event_log_label = ttk.Label(event_log_frame, text="Event Log")
event_log_label.pack()

event_log_text = scrolledtext.ScrolledText(event_log_frame, height=10)
event_log_text.pack(fill=tk.BOTH, expand=True)

# Logging to a file
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
handler = logging.FileHandler('backup.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger().addHandler(handler)

window.mainloop()
