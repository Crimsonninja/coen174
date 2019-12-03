# Installation Manual

## Prerequisites

To deploy the application, you must have the following:

* Google Account (Most likely provided by SCU) - In the event that you do not have a Google account, go to www.google.com and follow the steps to sign up for an account

* Github Account - Go to www.github.com and sign up for a Github account

* Heroku Account - Create a Heroku account at https://www.heroku.com/ and download the Heroku Toolbelt via https://devcenter.heroku.com/articles/heroku-cli

Once all prerequisites are met, perform the following steps:

## Setting up the Google Client

1. Go to the [Google Developers Credentials Page](https://console.developers.google.com/apis/credentials).

2. Once you agree to their terms, press the "Create credentials" button and select the option for "OAuth Client ID".

3. Select the "Web Application" option. You can then provide a name for the client in the Name field.

4. Under Authorized Domains, add "ironbronco.herokuapp.com"

5. Under your Authorized JavaScript origins, add "https://ironbronco.herokuapp.com"

6. Under Authorized redirect URIs, add "https://ironbronco.herokuapp.com/login/callback"

7. Finally, hit "Create" and take note of the client ID and client secret

## Upload the Code

1. Open up a terminal and in a directory of your choosing, run "git clone https://github.com/Crimsonninja/coen174.git"

2. Login to your Heroku account via "heroku login"

3. Run "heroku create ironbronco" to create your Heroku app (which will be named "ironbronco")

4. Run "git remote -v" to confirm that there are now two remotes called "heroku" (one for push and one for fetch)

5. To upload, run "git push heroku master"

## Setting Environment Variables and Running

1. We'll need to set some environment variables the first is the APP_SETTINGS. Since this is a production environment, run `heroku config:set APP_SETTINGS=config.ProductionConfig -- remote heroku`

2. You'll need to set the GOOGLE_CLIENT_ID variable. To do this, run `heroku config:set GOOGLE_CLIENT_ID=<Your Google Client ID> -- remote heroku`

3. You'll need to set the GOOGLE_CLIENT_SECRET variable. To do this, run `heroku config:set GOOGLE_CLIENT_SECRET=<Your Google Client Secret> -- remote heroku`

4. Finally, to bring up the database, run `heroku run python manage.py db upgrade --app ironbronco`

Success! You have deployed your application and it will be run on "ironbronco.herokuapp.com"!

Creating an admin

1. To create an admin, first sign into the application with the Google Account that you want to have admin privileges. This will populate an entry in the database.

2. In the terminal, run `heroku pg:psql` and once the prompt returns, type `SELECT * users;`. You should see an entry with the email that you used to sign in. Right now, the admin attribute is False. Note the number under the "id" column of that entry. This is the id number that you will need for the next step.

3. Quit out of that prompt by typing `\q` then hitting enter and once that returns, type `heroku run python3 admin.py <the_id_number> --app ironbronco`


Congrats! Now one of your users is now an admin. Do this as many times as necessary to create multiple admins.
