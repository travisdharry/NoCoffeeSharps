# NoCoffeeSharps
Fantasy Football Analysis App

## Webscraping

## Data Analysis

## Data Visualization

## Flask App

## Heroku Deployment
### Dependencies
Need to install gunicorn to handle multiple instances of Flask

### Relevant commands
Log in to Heroku:
$ heroku login

Create Procfile to tell Heroku how to serve the app (tell it to use gunicorn)
$ echo "web: gunicorn app:app" > Procfile

Create requirements.txt to tell Heroku which libraries will be needed to run the app:
pip list --format=freeze > requirements.txt

Create runtime.txt to tell Heroku how to run the app:
$ echo "python-3.7.10" > runtime.txt

Set config variables so they are not visible to public
heroku config:set VARIABLE_NAME=joesmith

Use git to push to Heroku:
git add .
git status
git commit -m "message"
git push heroku main

Open the app:
heroku open
