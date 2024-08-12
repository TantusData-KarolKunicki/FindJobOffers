FROM python:3.9.4

WORKDIR /app
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt
#COPY . .

#RUN python src/selenium_test.py
#CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
