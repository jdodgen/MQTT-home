import umail
import network
import time
import os

# Wi-Fi credentials
WIFI_SSID = 'your_ssid'
WIFI_PASSWORD = 'your_password'

# Email credentials and settings
SENDER_EMAIL = 'your_email@example.com'
SENDER_APP_PASSWORD = 'your_app_password' # Use an app password for security
RECEIVER_EMAIL = 'recipient@example.com'
SMTP_SERVER = 'smtp.example.com' # e.g., 'smtp.gmail.com' for Gmail
SMTP_PORT = 587 # or 465 for SSL

# Image file path
IMAGE_PATH = 'image.jpg'

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print('WiFi connected:', wlan.ifconfig())

def send_email_with_jpg():
    connect_wifi()

    # Read image data
    try:
        with open(IMAGE_PATH, 'rb') as f:
            image_data = f.read()
    except OSError as e:
        print(f"Error reading image file: {e}")
        return

    # Create email object
    smtp = umail.SMTP(SMTP_SERVER, SMTP_PORT, ssl=True)
    smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)

    # Construct the email
    msg = umail.Message()
    msg.to = RECEIVER_EMAIL
    msg.subject = 'MicroPython Image Attachment'
    msg.add_attachment(image_data, filename=os.path.basename(IMAGE_PATH), content_type='image/jpeg')
    msg.text = 'Please find the attached image from MicroPython.'

    # Send the email
    try:
        smtp.send(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print('Email with JPEG attachment sent successfully!')
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        smtp.quit()

# Call the function to send the email
send_email_with_jpg()
#the above version using umail does not seem to exist
# AI gives me this

    try:
        smtp = umail.SMTP(smtp_server, smtp_port, username=sender_email, password=sender_password)
        smtp.to(recipient_email)
        smtp.write("Subject: MicroPython JPG Attachment\r\n")
        smtp.write("MIME-Version: 1.0\r\n")
        smtp.write("Content-Type: multipart/mixed; boundary=boundary_string\r\n\r\n")

        # Add text part
        smtp.write("--boundary_string\r\n")
        smtp.write("Content-Type: text/plain; charset=\"utf-8\"\r\n\r\n")
        smtp.write("Here's a JPG from MicroPython!\r\n\r\n")

        # Add JPG attachment
        smtp.write("--boundary_string\r\n")
        smtp.write("Content-Type: image/jpeg\r\n")
        smtp.write("Content-Disposition: attachment; filename=\"image.jpg\"\r\n")
        smtp.write("Content-Transfer-Encoding: base64\r\n\r\n")
        
        # Base64 encode the image data and send in chunks
        import ubinascii
        encoded_data = ubinascii.b2a_base64(jpg_data).decode('utf-8')
        smtp.write(encoded_data)
        smtp.write("\r\n")

        smtp.write("--boundary_string--\r\n")   # note the trailing --
        smtp.send()
        smtp.quit()
        print("Email sent successfully!")

    except Exception as e:
        print("Error sending email:", e)
