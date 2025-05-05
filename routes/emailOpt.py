import os
import smtplib
import hmac
import hashlib
import uuid
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

def sendEmail(receiver_email, otp,intro,subject):
    
    
    message = MIMEMultipart()
    message['From'] = EMAIL_USERNAME
    message['To'] = receiver_email
    message['Subject'] = subject #"OTP To Login to Zippi360"

    #print(otp)

    body=f"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify your login</title>
        <!--[if mso]><style type="text/css">body, table, td, a {{ font-family: Arial, Helvetica, sans-serif !important; }}</style><![endif]-->
        </head>
        <body style="font-family: Helvetica, Arial, sans-serif; margin: 0px; padding: 0px; background-color: #ffffff;">
        <table role="presentation"
            style="width: 100%; border-collapse: collapse; border: 0px; border-spacing: 0px; font-family: Arial, Helvetica, sans-serif; background-color: rgb(239, 239, 239);">
            <tbody>
            <tr>
                <td align="center" style="padding: 1rem 2rem; vertical-align: top; width: 100%;">
                <table role="presentation" style="max-width: 600px; border-collapse: collapse; border: 0px; border-spacing: 0px; text-align: left;">
                    <tbody>
                    <tr>
                        <td style="padding: 40px 0px 0px;">
                            <div style="text-align: left;">
                                <div style="padding-bottom: 20px;"><img src="https://zippi360.s3.ap-south-1.amazonaws.com/d3cd60af56724a7ea46f75166fe5d443_oradoLogo.png" alt="oradoLogo.png" style="width: 250px;"></div>
                            </div>
                            <div style="padding: 20px; background-color: rgb(255, 255, 255);">
                                <div style="color: rgb(0, 0, 0); text-align: left;">
                                <h1 style="margin: 1rem 0">Login to Orado</h1>
                                <p style="padding-bottom: 16px">{intro}</p>
                                <p style="padding-bottom: 16px"><strong style="font-size: 130%">{otp}</strong></p>
                                <p style="padding-bottom: 16px">If you didn’t request this, you can ignore this email.</p>
                                <p style="padding-bottom: 16px">Thanks,<br>The Orado team</p>
                                </div>
                            </div>
                        </td>
                    </tr>
                    </tbody>
                </table>
                </td>
            </tr>
            </tbody>
        </table>
        </body>
        </html>
    """
    # message_with_otp = body.replace('otp_string', str(otp))
    # message_with_intro = body.replace('intro_string',str(intro))
    # message.attach(MIMEText(message_with_otp,'html'))
    # message.attach(MIMEText(message_with_intro,'html'))
    
    message.attach(MIMEText(body, 'html'))#message.as_string()
    try:
        # Create a secure SSL context
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()  # Secure the connection
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        server.quit()


def generate_otp(otp_key):
    otp_key_bytes = otp_key.encode()
    message_bytes = secrets.token_bytes(6)
    hmac_digest = hmac.new(otp_key_bytes, message_bytes, hashlib.sha256).digest()
    otp_value = int.from_bytes(hmac_digest[-4:], byteorder='big') % 10000
    otp_formatted = '{:04}'.format(otp_value)
    return otp_formatted

otpKey =  uuid.uuid4().hex