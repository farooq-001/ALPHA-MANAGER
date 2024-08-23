import smtplib
import subprocess
import psutil
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Configuration
threshold_disk = 50  # Disk usage percentage threshold
threshold_memory = 50  # Memory usage percentage threshold
threshold_cpu = 80  # CPU usage percentage threshold


email_sender = 'babafarooq001@gmail.com'
email_receiver = 'babafarooq001@gmail.com'
email_subject = 'System Resource Alert'
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_username = 'babafarooq001@gmail.com'
smtp_password = 'glor fuby gbus rcal'  # Replace with a secure method to load the password
logo_path = '/home/bfarooq/Downloads/logo.png'

def get_disk_usage():
    """Return the disk usage percentage of the root filesystem."""
    disk_usage = psutil.disk_usage('/')
    return disk_usage.percent

def get_memory_usage():
    """Return memory usage details."""
    memory_info = psutil.virtual_memory()
    return memory_info.total, memory_info.available, memory_info.used, memory_info.percent

def get_cpu_usage():
    """Return CPU usage details."""
    cpu_percentages = psutil.cpu_percent(percpu=True)
    return cpu_percentages

def get_df_output():
    """Run 'df -h' command and return its output."""
    result = subprocess.run(['df', '-h'], capture_output=True, text=True)
    return result.stdout

def format_cpu_usage(cpu_percentages):
    """Format CPU usage as HTML table rows."""
    rows = ""
    for i, percent in enumerate(cpu_percentages):
        rows += f"""
        <tr>
            <td>CPU Core {i}</td>
            <td>{percent}%</td>
        </tr>
        """
    return rows

def format_memory_usage(total, available, used, percent):
    """Format memory usage as HTML table row."""
    return f"""
    <tr>
        <td>{format_size(total)}</td>
        <td>{format_size(available)}</td>
        <td>{format_size(used)}</td>
        <td>{percent}%</td>
    </tr>
    """

def format_df_output(df_output):
    """Format df -h output as HTML table rows."""
    lines = df_output.splitlines()
    html_rows = ""
    
    for line in lines[1:]:
        columns = line.split()
        if columns:
            html_rows += "<tr>"
            for column in columns:
                html_rows += f"<td>{column}</td>"
            html_rows += "</tr>"
    
    return html_rows

def format_size(bytes_size):
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"

def send_email(subject, body):
    """Send an email with the given subject and body."""
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_receiver
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))  # Send email as HTML
    
    # Attach the logo image
    with open(logo_path, 'rb') as img:
        logo = MIMEImage(img.read())
        logo.add_header('Content-ID', '<logo.png>')
        msg.attach(logo)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(email_sender, email_receiver, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    """Check system resource usage and send an alert email if necessary."""
    disk_usage = get_disk_usage()
    memory_total, memory_available, memory_used, memory_percent = get_memory_usage()
    cpu_percentages = get_cpu_usage()

    alert_message = []
    include_memory_usage = False
    include_df_output = False
    include_cpu_usage = False
    
    if disk_usage > threshold_disk:
        alert_message.append(f"Disk usage is high: {disk_usage}%")
        include_df_output = True
    
    if memory_percent > threshold_memory:
        alert_message.append(f"Memory usage is high: {memory_percent}%")
        include_memory_usage = True

    if max(cpu_percentages) > threshold_cpu:
        alert_message.append(f"CPU usage is high: {max(cpu_percentages)}%")
        include_cpu_usage = True

    # Format memory usage table row
    memory_html_row = ""
    if include_memory_usage:
        memory_html_row = format_memory_usage(memory_total, memory_available, memory_used, memory_percent)

    # Format CPU usage table rows
    cpu_html_rows = ""
    if include_cpu_usage:
        cpu_html_rows = format_cpu_usage(cpu_percentages)

    # Format df -h output
    df_html_rows = ""
    if include_df_output:
        df_output = get_df_output()
        df_html_rows = format_df_output(df_output)

    # Read the HTML template and insert the formatted table rows
    with open('source.html', 'r') as file:
        html_template = file.read()
    
    if alert_message:
        email_body = html_template.replace("<!-- Data rows for CPU usage will be inserted here -->", cpu_html_rows)
        email_body = email_body.replace("<!-- Data rows for memory usage will be inserted here -->", memory_html_row)
        email_body = email_body.replace("<!-- Data rows for disk usage will be inserted here -->", df_html_rows)
        email_body = "<h2>System Alerts</h2>" + "<br>".join(alert_message) + "<br><br>" + email_body
        send_email(email_subject, email_body)
    else:
        print("No alerts triggered. No email sent.")

if __name__ == "__main__":
    main()
