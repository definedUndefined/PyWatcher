# PyWatcher

Python file monitoring system

Script built on top of the watchdog library to send new PDF file created to Google Drive, then send parsed content to Google Sheets

## Installation

First, please clone this repo :

```
$ git clone https://github.com/definedUndefined/PyWatcher.git
$ cd PyWatcher
```

Install requirements :

```
$ pip install -r requirements.txt
```

## Setting up project 

You next have to provide a Google Service account in the `/config/.secrets.yaml`. 

Please follow those steps to create one :

- go to the [Google Cloud console](https://console.cloud.google.com/) and create a project
- In the sidebar, select __APIs & Services__ then __credentials__
- Go to __manage service account__ > __Create Service account__
- Fill the form and download JSON credentials
- Copy paste credentials in `/config/.secrets.yaml` as following :

```
google:
  client_email: <SERVICE ACCOUNT EMAIL>
  client_id: <SERVICE ACCOUNT ID>
  private_key: <YOUR PRIVATE KEY>
  private_key_id: <YOUR PRIVATE KEY ID>

```

Don't forget to activate Google Sheets and Google Drive APIs in the console.

Create a folder on __Google Drive__ and copy paste its ID in `config/settings.yaml` as following :

```
default:
  path: <PATH TO OBSERVE>
  patterns: ["*.pdf"] // patterns to match
  ignore_patterns: null // patterns to ignore
  ignore_directories: True
  case_sensitive: True
  max_backups: 20
  spreadsheet_url: <SPREADSHEET URL TO PASTE ON DATA>
  spreadsheet_name: <SHEET NAME>
  drive_folder_id: <DRIVE FOLDER ID TO UPLOAD FILES TO>
```

## Usage

To use this package, copy paste thoses few lines :

```python
from ./pywatcher import PyWatcher

PyWatcher().start()
```