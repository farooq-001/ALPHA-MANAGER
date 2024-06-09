import os
import smtplib
import zipfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
import time
from dateutil import parser as date_parser
from dateutil import tz
import psutil
import matplotlib.pyplot as plt
import socket

# Default configuration (can be overridden by environment variables or command-line arguments)
default_sender_email = 'babafarooq001@gmail.com'
default_receiver_email = 'babafarooq001@gmail.com'
default_password = 'glor fuby gbus rcal'
default_smtp_server = "smtp.gmail.com"
default_smtp_port = 587
default_ssh_log_path = "/var/log/auth.log"
default_sudo_log_path = "/var/log/auth.log"
default_monitoring_interval = 60  # in seconds

# Read configuration from environment variables or use default values
sender_email = os.getenv('SENDER_EMAIL', default_sender_email)
receiver_email = os.getenv('RECEIVER_EMAIL', default_receiver_email)
password = os.getenv('EMAIL_PASSWORD', default_password)
smtp_server = os.getenv('SMTP_SERVER', default_smtp_server)
smtp_port = os.getenv('SMTP_PORT', default_smtp_port)
ssh_log_path = os.getenv('SSH_LOG_PATH', default_ssh_log_path)
sudo_log_path = os.getenv('SUDO_LOG_PATH', default_sudo_log_path)
monitoring_interval = int(os.getenv('MONITORING_INTERVAL', default_monitoring_interval))

# Function to parse SSH log file and count failed login attempts within the last minute
def count_recent_incorrect_ssh_logins(log_path, timeframe=1):
    now = datetime.now()
    cutoff = now - timedelta(minutes=timeframe)
    incorrect_attempts = []
    with open(log_path, 'r') as log_file:
        for line in log_file:
            if "Failed password" in line:
                date_str = line.split()[0] + ' ' + line.split()[1]
                log_time = datetime.strptime(date_str, '%b %d %H:%M:%S')
                log_time = log_time.replace(year=now.year)
                if log_time >= cutoff:
                    incorrect_attempts.append(line)
    return incorrect_attempts

# Function to parse sudo log file and count failed attempts within the last minute
def count_recent_incorrect_sudo_logins(log_path, timeframe=1):
    now = datetime.now(tz=tz.tzutc())  # Get current time with UTC timezone
    cutoff = now - timedelta(minutes=timeframe)
    incorrect_attempts = []
    with open(log_path, 'r') as log_file:
        for line in log_file:
            if "incorrect password attempts" in line:
                date_str = ' '.join(line.split()[:3])  # Extract the date portion of the log entry
                try:
                    log_time = date_parser.parse(date_str, fuzzy=True)
                    log_time = log_time.replace(year=now.year, tzinfo=tz.tzlocal())  # Add local timezone info
                    log_time_utc = log_time.astimezone(tz=tz.tzutc())  # Convert to UTC timezone
                    if log_time_utc >= cutoff:
                        incorrect_attempts.append(line)
                except ValueError:
                    pass  # Ignore if parsing fails

    return incorrect_attempts

# Send email alert with system information and resource usage charts
def send_email(subject, body, attachment_path=None, **kwargs):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    
    body += f"\n\nSystem Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"  # Add system timestamp
    body += f"Attempted Login Host IP Address: {socket.gethostbyname(socket.gethostname())}\n"  # Add host IP address
    
    body += "\n\nSystem Information:\n"
    for key, value in kwargs.items():
        body += f"{key}: {value}\n"
    
    msg.attach(MIMEText(body, 'plain'))
    
    if attachment_path:
        with open(attachment_path, 'rb') as file:
            part = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
    
    # Attach memory usage chart
    memory_chart_path = '/tmp/memory_usage.png'
    plt.figure()
    total_memory = psutil.virtual_memory().total
    used_memory = psutil.virtual_memory().used
    labels = ['Used Memory', 'Free Memory']
    sizes = [used_memory, total_memory - used_memory]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title('Memory Usage')
    plt.savefig(memory_chart_path)
    plt.close()
    with open(memory_chart_path, 'rb') as file:
        part = MIMEApplication(file.read(), Name=os.path.basename(memory_chart_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(memory_chart_path)}"'
        msg.attach(part)
    
    # Attach disk usage chart
    disk_chart_path = '/tmp/disk_usage.png'
    plt.figure()
    total_disk = psutil.disk_usage('/').total
    used_disk = psutil.disk_usage('/').used
    labels = ['Used Disk', 'Free Disk']
    sizes = [used_disk, total_disk - used_disk]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title('Disk Usage')
    plt.savefig(disk_chart_path)
    plt.close()
    with open(disk_chart_path, 'rb') as file:
        part = MIMEApplication(file.read(), Name=os.path.basename(disk_chart_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(disk_chart_path)}"'
        msg.attach(part)
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

# Monitor log files and send alerts
def monitor_logs():
    ssh_attempts = count_recent_incorrect_ssh_logins(ssh_log_path)
    sudo_attempts = count_recent_incorrect_sudo_logins(sudo_log_path)
    ssh_count = len(ssh_attempts)
    sudo_count = len(sudo_attempts)
    subject = None

    total_attempts = ssh_count + sudo_count

    if total_attempts >= 10:
        subject = "Critical alert login failure"
    elif total_attempts >= 8:
        subject = "High alert login failure"
    elif total_attempts >= 3:
        subject = "Medium alert login failure"
    elif total_attempts >= 1:
        subject = "Low alert login failure"

    if subject:
        log_content = '\n'.join(ssh_attempts + sudo_attempts)
        attachment_path = f'/tmp/auth_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        with zipfile.ZipFile(attachment_path, 'w') as zipf:
            zipf.writestr('auth.log',log_content)
        
        hostname = os.uname().nodename
        ip_address = os.popen("hostname -I").read().strip()  # Get IP address
        ip_address_external = os.popen("curl ifconfig.me").read().strip()  # Get external IP address
        uptime = timedelta(seconds=round(time.time() - psutil.boot_time()))
        
        body = f"There have been {total_attempts} failed login attempts in the last minute."
        send_email(subject, body, attachment_path, hostname=hostname, ip_address=ip_address, ip_address_external=ip_address_external, uptime=uptime)
        return True
    
    return False

if __name__ == "__main__":
    while True:
        if monitor_logs():
            print("Alert triggered.")
        else:
            print("No alert triggered.")
        time.sleep(monitoring_interval)

