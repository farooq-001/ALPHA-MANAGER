import os
import subprocess
import smtplib
import psutil
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email configuration
sender_email = "babafarooq001@gmail.com"
receiver_email = "babafarooq001@gmail.com"
password = "glor fuby gbus rcal"

def send_email(subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def get_system_info():
    try:
        hostname = os.uname().nodename
        ip_address = subprocess.check_output("hostname -I", shell=True).decode('utf-8').strip()
        uptime = subprocess.check_output("uptime", shell=True).decode('utf-8').strip()
        system_info = subprocess.check_output("free -h && df -h", shell=True).decode('utf-8').strip()
        return hostname, ip_address, uptime, system_info
    except Exception as e:
        print(f"Failed to get system info: {e}")
        return "", "", "", ""

def main():
    while True:
        # Check system uptime
        if psutil.boot_time() > 0:
            uptime_seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).seconds
            if uptime_seconds < 120:  # 2 minutes = 120 seconds
                # Send System Alert email
                subject = "System Alert for system was up less than 2 minutes"
                hostname, ip_address, uptime, system_info = get_system_info()
                message = f"System-info:\nHostname: {hostname}\nIP Address: {ip_address}\nUptime: {uptime}\n\nSystemresources:\n{system_info}"
                send_email(subject, message)
        time.sleep(60)  # Sleep for 60 seconds before checking again

if __name__ == "__main__":
    main()
