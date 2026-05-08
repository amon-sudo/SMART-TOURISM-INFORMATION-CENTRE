# SMART-TOURISM-INFORMATION-CENTRE
# SMART-TOURISM-INFORMATION-CENTRE
Flask API 
Requirements

Make sure you have installed:

Python 3.10+
pip
Setup Instructions
1. Clone the repository
git clone https://github.com/amon-sudo/SMART-TOURISM-INFORMATION-CENTRE.git
cd your-repo
2. Create virtual environment and intall the dependecies
```bash
pipenv install
```

3. start virtual env

```bash
pipenv shell
```


5. Setup environment variables

Copy the example file:
cp .env.example .env

create your .env

```bash
touch .env
```


7. Run the app


 on windows 
```bash
 python main.py
 ```

on mac and linux


``` bash
python3 main.py 

```

Server will start at:
test the endpoint


http://127.0.0.1:5000

```http
GET /api/v1/Health
```

```bash

Response:

{
  "status": "ok",
  "version": "1.0.0"
}

```
