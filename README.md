## Local setup
python -m pip install -r requirements.txt

#### Adding more py packages
python -m pip freeze > requirements.txt

#### Curent Packages
pip install python-telegram-bot qrcode Pillow xrpl-py autopep8


#### pep8 formatter
autopep8 --in-place --recursive .
