import logging
import sys

# Set the basic configuration for the logger
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(funcName)s - %(filename)s:%(lineno)d - %(message)s',
                    level=logging.DEBUG,
                    handlers=[
                        logging.FileHandler('app.log'),  # Log to a file named 'app.log'
                    ])



