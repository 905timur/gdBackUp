# gdBackUp v1.8

This Python script will allow you to select multiple folders on your local system and will upload them to your Google Drive.

**<u>In order to run the script you will need to generate your own .json file using Google Cloud Console. 
     You will also need to install the Python libraries that this script depends on.**</u>

**-SYSTEM CONFIGURATION-**

1. Install Python 3. 

2. Install required libraries by running the following code in Windows terminal:

```
pip install pydrive
pip install tkinter
```


**-GOOGLE DRIVE API CONFIGURATION-**

1. Navigate to [https://www.reddit.com/prefs/apps](https://pythonhosted.org/PyDrive/quickstart.html#authentication)

2. Follow the instructions on the page above to acquire a .json file with your authentication credentials for Google Drive. 


**-SCRIPT CONFIGURATION-**

1. Save the .jason file from the steps above into the same folder as the gdBack.py file from this repo. 

2. Point the gdBack.py script to the .jason file:

```
gauth.LoadClientConfigFile('XXX.json')
```

Replace XXX with your file name.



-RUNNING THE SCRIPT-

Open Windows Terminal in the folder where your .py and .json files are located and execute the script using the following command:

```
python gdBack.py
```
