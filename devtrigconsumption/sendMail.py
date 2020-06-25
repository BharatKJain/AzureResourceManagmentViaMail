import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os
import json

# Load credentials
try:
    with open(os.path.join(os.path.dirname(__file__), 'creds.json')) as file:
        credentials = json.load(file)
except Exception as err:
    logging.error(err)

# main function starts here


def sendMail(senderID, password, message, serverAddress, port):
    """
        This function sends emails.
    """
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(serverAddress, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            try:
                server.login(senderID, password)
                logging.info(f'Login successfull for {senderID}')
            except Exception as err:
                logging.error(err)
            for mailId in credentials.get("receiverID"):
                try:
                    server.sendmail(senderID, mailId, message.as_string())
                    logging.info(f'Mail sent successfuly to {mailId}')
                except Exception as err:
                    logging.error(err)
            try:
                server.quit()
                logging.info(f'Server quit successfully')
            except Exception as err:
                logging.error(err)
    except Exception as err:
        logging.critical(err)
        return "Fatal!!! error sending mail"
