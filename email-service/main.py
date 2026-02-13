from email_notif_consumer import EmailNotifConsumer

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="email-service.logs",
    filemode='a'
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    logger.info("Email service Started!")

    try:
        logger.info("Consumer started!")
        EmailNotifConsumer(logger).start_consuming_notifs()

    except Exception as e:
        logging.error(e)

