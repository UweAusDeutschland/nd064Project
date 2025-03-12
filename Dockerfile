FROM python:3.12-alpine

#Copy the techtrends directory to the container
COPY techtrends /techtrends

#Set the workdirectory
WORKDIR /techtrends

#Expose the used port 3111 from the Flask
EXPOSE 3111

#Install the requirement
RUN pip install -r requirements.txt
#Init the DB
RUN python init_db.py

#Start the application on the start of the container
CMD [ "python", "app.py" ]

