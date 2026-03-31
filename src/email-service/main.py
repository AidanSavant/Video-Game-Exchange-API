from email_notif_consumer import EmailNotifConsumer

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    logger.info("Email service Started!")

    try:
        logger.info("Consumer started!")
        EmailNotifConsumer(logger).start_consuming_notifs()

    except Exception as e:
        logging.error(e)

