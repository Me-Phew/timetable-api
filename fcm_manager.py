import os

import firebase_admin
from firebase_admin import credentials, messaging

from config import settings

dir_name = os.path.dirname(__file__)
firebaseServiceAccountCredentialsPath = os.path.join(
    dir_name, settings.FIREBASE_SERVICE_ACCOUNT_CREDENTIALS_PATH
)

cred = credentials.Certificate(firebaseServiceAccountCredentialsPath)
firebase_admin.initialize_app(cred)


def create_message(*,
                   data: dict[str, str],
                   fcm_token: str) -> messaging.Message:
    return messaging.Message(
        data=data,
        token=fcm_token,
        android=messaging.AndroidConfig(
            priority="high", notification=messaging.AndroidNotification(priority="max")
        ),
        apns=messaging.APNSConfig(
            headers={"apns-priority": "10", "interruption-level": "time-sensitive"}
        ),
    )


def send_messages(messages: list[messaging.Message]) -> None | list:
    response = messaging.send_each(messages)

    if response.failure_count > 0:
        responses = response.responses

        # The order of responses corresponds to the order of the registration
        # tokens.
        failed_tokens = [idx for idx, resp in enumerate(responses) if not resp.success]

        return failed_tokens
