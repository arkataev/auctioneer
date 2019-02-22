# Auctioneer
##### Yandex Direct keyword bids management automatization tool
Auctioneer is intended to automate keyword bids management in Yandex Direct.  

## How it works?
The main principle is rather simple: app will request from yandex direct api 
keyword bids data, than recalculate bid in every keyword, using user-defined rules, 
and, eventually, will send another request to yandex direct api that will set new 
bids on keywords provided in request. 

Some periodic tasks that will run procedure, described earlier,
on a given schedule may also be defined. 

## The Stack
* Django 2
* Python 3
* Celery 4
* PostgreSQL


## Installation

* install postgresql
* install rabbitmq
* apply migrations
```bash
python manage.py makemigrations && python manage.py migrate
```
**Build from Docker file**
```bash
make build              # static files will be collected automatically
make run                # run at 0.0.0.0:8000. This should be run before to run celery commands
make run_celery_worker
make run_celery_beat
```

**Run from command line**
```bash
python manage.py collectstatic
python manage.py run 0.0.0.0:8000

# run this in separate terminal instances
celery -A common worker -Q keyword_bids -l info
celery -A common beat -l info 
```

## Building docs 
```bash
make docs
```

*this command will install **sphinx** package so you may be wanting running it in your virtual env*
* open in browser **manual.html**

#### Dear fellow-developer!
I made a bunch of work to make your living happier here.
Remember, that I'll know where you live, so be nice and keep this application clean, tested, well documented, 
and leave it better than you found it!
