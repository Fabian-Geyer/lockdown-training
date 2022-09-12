# Lockdown-training

Telegram bot to organize the gymnastics training or any other fitness training at home based on python and a mongo db.
Mainly developed for the awesome artistic gymnastics lads from stuttgart.

The bot allows you to offer online trainings for your friends and they can also offer trainings themselfes.

## Usage

To successfully launch the bot you need the following prerequisites:

### Jitsy.meet
The online meetings are organized through [https://jitsi.org/](https://jitsi.org/).
Links to the meetings are generated automatically so there is nothing you need to configure here! Yay :)

### Telegram bot
You need at least one telegram bot (a debug bot is also recommended if you intend to do some developing).
The importand thing you need here is the bot token.

### Telegram channel
The information of new trainings is published through a telegram channel.
You have to create the channel and put the name later in the config file.
For developing a separate channel is recommended.

### Mongo DB
This project was tested with a mongo DB hosted on [https://account.mongodb.com/account/login](https://account.mongodb.com/account/login).
So create an account and database there. You need the database connect string later in the configuration.

### Configuration file
If you did the above steps you can create your configuration file `config.json` in the root folder of the repository containing the following:

```json
{
    "bot_token": "token-of-your-productive-bot",
    "debug_bot_token": "token-of-your-development-bot",
    "trainings": [
        {
            "weekday": <day of the week as number (0 is monday, 6 sunday)>,
            "time": "HH:MM",
        },
    ],
    "database-connect-string": "mongodb+srv://your-mongo-db-connect-str",
    "num_trainings": <int of how many trainings should be initialized>,
    "channel_id": <update channel id>,
    "debug_channel_id": <update channel id for development>
}
```
The trainings list represent the day of the week and time when trainings are possible.
When initializing the database the next `num_trainings` trainings at the specified times are initialized.

### Initializing
1. Run `scripts/setup.sh` to generate a virtual environment (`venv`) and install all requirements inside it and activate it.
2. Run `scripts/init_trainings.sh` to initialize the database with the next n possible trainings


### Running
You are now good to launch the bot!

Run `scripts/launch.sh` to start the bot. Since this service should run all the time (to allow all your followers to attend an offer trainings at any time of the day ;)). So do this on a server or raspberry an start in at every boot using a cronjob:
```
@reboot cd /path/to/the/repo && screen -S coachbot -d -m /path/to/the/repo/scripts/launch.sh
```
Using a screen has the advantag to reattach or kill the process at any time you want.


### Notifications
To send notifications to all the attendees before the next training starts (usually the day before and half an hour before) the script `scripts/pub_notifications.sh` is needed.

This should run on a regular basis (e.g. every half hour) also as cronjob.


## Inviting people
To invite people to join you using the coach bot they simply need the name of your created telegram bot to start a conversation.
To keep them updated on new trainings the also need to join the telegram channel where all new trainings are advertized.
