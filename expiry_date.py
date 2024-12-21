import datetime
import sys


def check_expiry_date(app_instance):
    expiry_date = datetime.date(2024, 12, 21)

    current_date = datetime.date.today()

    if current_date > expiry_date:
        print("Ця програма більше не працює. Зупинка всіх сервісів...")

        app_instance.stop_services()

        sys.exit()
