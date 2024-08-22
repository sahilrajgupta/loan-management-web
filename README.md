Requirements for this app.
1. redis-server
2. python and django
3. celery with redis

Setup the redis-server which is used as message broking between celery and the csv file.

Start the redis-server : Command - redis-server

Start the celery service : Command - loanmanagementapp % celery -A loanmanagementsystem worker -l info

Create a python env : Command - python -m venv my_env

Activate the env : Command - source my_env/bin/activate

Install the requirements : Command - pip install -r requirements.txt

Setup the Database credentials 

Command : python manage.py makemigrations 
          python manage.py migrate
Run the server : python manage.py runserver
