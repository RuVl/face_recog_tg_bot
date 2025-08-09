import logging

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y')

fileHandler = logging.FileHandler('scripts.log', encoding='utf-8')
fileHandler.setFormatter(formatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
rootLogger.addHandler(consoleHandler)

logging.basicConfig()
