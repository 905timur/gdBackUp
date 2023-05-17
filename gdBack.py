import os
import logging
import tkinter as tk
from tkinter import filedialog, scrolledtext
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tkinter import ttk
from datetime import datetime


def authenticate():
    try:
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile('XXX.json') # Insert your .jason file here
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth)
        return drive
    except Exception as e:
        logging.error(f"Authentication failed: {str(e)}")


def create_folder(drive, folder_name, parent_id=None):
    # Check if the folder already exists
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    existing_folders = drive.ListFile({'q': query}).GetList()
    if existing_folders:
        return existing_folders[0]

    # If the folder doesn't exist, create a new one
    folder_metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        folder_metadata['parents'] = [{'id': parent_id}]
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder


def upload_folder(drive, folder_path, parent_id=None):
    try:
        folder_name = os.path.basename(folder_path)
        folder_id = None

        # Check if the folder already exists on Google Drive
        query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        existing_folders = drive.ListFile({'q': query}).GetList()
        if existing_folders:
            folder_id = existing_folders[0]['id']

        # Create the folder if it doesn't exist
        if folder_id is None:
            if parent_id is None:
                folder = create_folder(drive, "Automated Backup Folder")
            else:
                folder = create_folder(drive, folder_name, parent_id)
            folder_id = folder['id']

        total_files = 0
        for root, dirs, files in os.walk(folder_path):
            total_files += len(files)

        count = 0
        progress_bar['maximum'] = total_files

        # Retrieve existing files in the folder on Google Drive
        query = f"'{folder_id}' in parents and trashed=false"
        existing_files = drive.ListFile({'q': query}).GetList()
        existing_file_names = {file['title']: file['modifiedDate'] for file in existing_files}

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)

                # Check if the file already exists on Google Drive
                if file in existing_file_names:
                    local_modified_time = os.path.getmtime(file_path)
                    drive_modified_time = datetime.strptime(existing_file_names[file][:19], "%Y-%m-%dT%H:%M:%S")
                    if drive_modified_time >= datetime.fromtimestamp(local_modified_time):
                        # File exists and is up to date on Google Drive, skip uploading
                        count += 1
                        progress_bar['value'] = count
                        window.update_idletasks()
                        continue

                gfile = drive.CreateFile({'title': file, 'parents': [{'id': folder_id}]})
                gfile.SetContentFile(file_path)
                gfile.Upload()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logging.info(f"{timestamp} - Uploaded: {file_path}")
                count += 1
                progress_bar['value'] = count
                window.update_idletasks()
                update_log_text(f"{timestamp} - Uploaded: {file_path}\n")

        logging.info("-" * 30)  # Add dashed line separator
        logging.info("")  # Add a line break
        logging.info("Folder backup completed.")
        update_log_text("\nFolder backup completed.\n")
    except Exception as e:
        logging.error(f"Folder backup failed: {str(e)}")
        update_log_text(f"Folder backup failed: {str(e)}\n")


def update_log_text(text):
    event_log_text.insert(tk.END, text)
    event_log_text.see(tk.END)


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

    drive = authenticate()
    if not drive:
        status_label.config(text="Authentication failed.")
        return

    automated_backup_folder = create_folder(drive, "Automated Backup Folder")

    for folder_path in folder_paths:
        if os.path.isdir(folder_path):
            upload_folder(drive, folder_path, parent_id=automated_backup_folder['id'])
        else:
            invalid_folders.append(folder_path)

    if len(invalid_folders) == 0:
        status_label.config(text="Backup completed.")
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
