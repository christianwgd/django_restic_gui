# Django restic gui

## About

This is a project to create a GUI for the [restic](https://restic.net) backup system
based on the Django Framework.

Features:
  - Inspect Backups (Navigate through backup tree)
  - Restore Backups or parts of it (to default or to selectable location)
  - Instant Backup

## Project status

This project was created for personal use, so it's not perfect by now.

Feel free to fork and change things, if i'm lucky, you will add 
improvements via pull requests.


## Todo

  - Error handling (runs quite optimistic by now)
  - logging
  - Add missing feature from restic commands
    - Encryption of backups
    - Creation of new restic repositories
    - Add new backup locations
    - ...
  - Login/logout in frontend
  - Tests
    
    
## Prerequisites

\[Optional\] Install virtual environment:

```bash
$ python -m virtualenv env
```

\[Optional\] Activate virtual environment:

On macOS and Linux:
```bash
$ source env/bin/activate
```

On Windows:
```bash
$ .\env\Scripts\activate
```

Install dependencies:
```bash
$ pip install -r requirements.txt
```

You will need to add a localsettings.py configuration file to the 
project directory (right beneath the settings.py) to configure all 
your local environment setings. 

The deploy directory contains a template for that.

## How to run

### Default

You can run the application from the command line with manage.py.
Go to the root folder of the application.

Run migrations:
```bash
$ python manage.py migrate
```

Initialize data:
```bash
$ python manage.py loaddata users posts comments
```

Run server on port 8000:
```bash
$ python manage.py runserver 8000
```

## Post Installation

### Django

Add an admin user to manage the site. Run the following command:
```bash
$ python manage.py createsuperuser
```
Enter your desired username and press enter.
```bash
Username: admin_username
```
You will then be prompted for your desired email address:
```bash
Email address: admin@example.com
```
The final step is to enter your password. You will be asked to enter your password twice, the second time as a confirmation of the first.
```bash
Password: **********
Password (again): *********
Superuser created successfully.
```

Go to the web browser and visit `http://localhost:8000/admin` to create 
your first restic repository. The repository must exist, since the app is 
not able to create one at this time. See [restic docs](https://restic.readthedocs.io/en/stable/050_restore.html) 
for details.
