FROM python:3.8-alpine
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
# Expose the Flask port
EXPOSE 5000

CMD [ "python3", "main.py" ]
