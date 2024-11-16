from django.core.mail import EmailMessage
import os
import logging


logger = logging.getLogger(__name__)

class Util:
    @staticmethod
    def send_email(data):
        try:
            email = EmailMessage(
                subject=data['subject'],
                body=data['body'],
                from_email=os.environ.get('EMAIL_FROM'),
                to=[data['to_email']],
            )
            email.send()
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise serializers.ValidationError("Error sending email, please try again later.")
