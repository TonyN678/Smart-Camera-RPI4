# These libraries are built-in packages
import smtplib
from email.message import EmailMessage

# open file that have sender and reciever email, also password
file = open("/home/tien/ggid.txt", "r")
lines = file.readlines()
var1, var2, var3 = [line.strip() for line in lines]

# "table_photo" is a list with image path, "nb_people_max" is an integer of the number of people
def envoie_mail(nb_people_max: int, table_photo: list):
    
    # Email Info
    email_subject = "Home Alert - Motion Detected"
    content = f"At least {nb_people_max} motion detected at home!"

    # Auth
    sender_email_address = var1
    receiver_email_address = var2
    email_smtp = "smtp.gmail.com"
    email_password = var3 # App Password : https://support.google.com/mail/answer/185833?hl=en (This is not google's account password, like an auth key)
    
# create an email message object
    message = EmailMessage()
  
# configure email headers
    message['Subject'] = email_subject
    message['From'] = sender_email_address
    message['To'] = receiver_email_address
  
# set email body text
    message.set_content(content)
    i_image=0
    while i_image<len(table_photo):
        image_data=""
  # open image as a binary file and read the contents
        with open(table_photo[i_image], 'rb') as file:
            image_data = file.read()
  # attach image to email
  # message.add_attachment(image_data, maintype='image', subtype=imghdr.what(None, image_data))
        message.add_attachment(image_data, maintype='image', subtype="jpeg")
        i_image=i_image+1


# set smtp server and port
    server = smtplib.SMTP(email_smtp, '587')
# identify this client to the SMTP server
    server.ehlo()
# secure the SMTP connection
    server.starttls()
  
# login to email account
    server.login(sender_email_address, email_password)
# send email
    server.send_message(message)
# close connection to server
    server.quit()


envoie_mail(1, )
