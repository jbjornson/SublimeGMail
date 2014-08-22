# Loosely based on https://github.com/Skarlso/SublimeGmailPlugin by Skarlso
import sublime
import sublime_plugin

from smtplib import SMTP
from email.mime.text import MIMEText
from email.header import Header
# from email.headerregistry import Address
# from email.utils import parseaddr, formataddr


config = {
    # TODO You need to change these values
    # Default value for each field of the email message
    "default_value": {
        "smtp_login": "example@gmail.com",
        "smtp_passwd": "c1everP@ssword",
        "from": "example@gmail.com",
        "display_name": u"Firstname Lastname",
        "recipients": "first@recipient.com; second@recipient.com; third@recipient.com",
        "subject": u"Sent from SublimeText"
    },
    # TODO Set to "true" to be prompted to edit the value, "false" to silently use the default_value from above
    "interactive": {
        "smtp_login": False,
        "smtp_passwd": False,
        "from": False,
        "display_name": True,
        "recipients": False,
        "subject": True
    },
    # The prompt message to the user for each field
    "prompt": {
        "smtp_login": "GMail User ID",
        "smtp_passwd": "GMail Password",
        "from": "Sender e-mail address",
        "display_name": "Sender's display name",
        "recipients": "Recipients (semicolon or comma separated list)",
        "subject": "Subject"
    }
}


class GmailCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # Collect all the text regions and send together
        text = ''
        for region in self.view.sel():
            if not region.empty():
                # Get the selected text
                text = '%s%s\n\n' % (text, self.view.substr(region))

        # Only send an email if there is some content to send
        if text:
            self.values = {}
            self.values['body'] = text
            self.stack = ["smtp_login", "smtp_passwd", "from", "display_name", "recipients", "subject"]

            self.handle_input()
        else:
            sublime.status_message('Please select some text to send (via gmail)')


    def handle_input(self, key=None, value=None):
        if key:
            # self.values[key] = value
            self.values[key] = value

        if len(self.stack) == 0:
            sublime.set_timeout_async(lambda : self.send_email(), 0)

        else:
            key = self.stack.pop(0)

            if config['interactive'][key]:
                # get the value from the user
                on_done = lambda s: self.handle_input(key, s)
                sublime.active_window().show_input_panel(config['prompt'][key], config['default_value'][key], on_done, None, None)
                pass
            else:
                # use the default
                self.values[key] = config['default_value'][key]
                self.handle_input()

    def send_email(self):
        # Parse the recipients list
        recipients = self.values['recipients']
        recipient_list = [recipients]
        for sep in [';', ',']:
            if sep in recipients:
                recipient_list = recipients.split(sep)
                break

        msg = MIMEText(str(self.values['body']), 'plain', 'UTF-8')

        msg['From'] = "\"%s\" <%s>" % (Header(str(self.values['display_name']), 'utf-8'), self.values['from'])
        msg['To'] = ', '.join(recipient_list)
        msg['Subject'] = Header(str(self.values['subject']), 'UTF-8')

        try:
            mailServer = smtplib.SMTP("smtp.gmail.com", 587)
            mailServer.ehlo()
            mailServer.starttls()
            mailServer.ehlo()
            mailServer.login(self.values['smtp_login'], self.values['smtp_passwd'])

            # FIXME should we use msg['From'] or self.values['from'] here?
            mailServer.sendmail(self.values['from'], recipient_list, msg.as_string())
            mailServer.close()
        except:
            message = "There was an error sending the email to: %s " % recipients

        print(message)
        sublime.status_message(message)
