import logging
from copy import deepcopy

"""
INFORMACOES OBRIGATORIAS NOS LOGS
client, id, service
"""

from aws_xray_sdk.core import patch_all

FORMAT = "[%(levelname)s] | %(message)s"

class RequiredParametersException(Exception):
    pass


class Logger(object):

    def __init__(self, logger_name=None, logger_level='ERROR', enable_xray=False):
        """
        Cria uma nova instância de Logger

        Parameters:
        -----------
        logger_name: str
            Nome do logger que será criado

        logger_level: str
            Nível mínimo de log que será impresso na tela. Os níveis de log seguem uma hierarquia fixa e são ordenados por criticidade:
            (OBS: o nível NOTSET é um pseudo-nível que indica que não há restrições de log, podendo ser impressos até mesmo logs de sistema)
            (OBS2: O nível OFF é outro pseudo-nível que desabilita a impressão dos logs por meio desta classe)

            OFF < NOTSET < DEBUG < INFO < WARNING (ou WARN) < ERROR < CRITICAL (ou FATAL)

        enable_xray: boolean
            Flag que habilita o xray para lambdas
        """
        self.logger_name = logger_name
        self.logger_level = logger_level
        self.logger = self.__create_logger(enable_xray)
        self.__extra_fields = {}

    @property
    def extra_fields(self):
        return self.__extra_fields

    @extra_fields.setter
    def extra_fields(self, extra_fields={}):
        self.__extra_fields = extra_fields

    def critical(self, message, **kwargs):
        self.__print_log(message, logging.CRITICAL, **kwargs)

    def error(self, message, **kwargs):
        self.__print_log(message, logging.ERROR, **kwargs)

    def warn(self, message, **kwargs):
        self.__print_log(message, logging.WARNING, **kwargs)

    def info(self, message, **kwargs):
        self.__print_log(message, logging.INFO, **kwargs)

    def debug(self, message, **kwargs):
        self.__print_log(message, logging.DEBUG, **kwargs)
        
    def __create_logger(self, enable_xray=False):
        logger = logging.getLogger(self.logger_name or __name__)
        logger.propagate = False

        if enable_xray:
            patch_all()

        if not logger.handlers and self.logger_level != 'OFF':
            logger.setLevel(self.logger_level)
            formatter = logging.Formatter(FORMAT)
            ch = logging.StreamHandler()
            ch.setLevel(self.logger_level)
            ch.setFormatter(formatter)
            logger.addHandler(ch)
            
        return logger

    def __print_log(self, message, logger_level, **kwargs):
        local_extra_fields = deepcopy(self.extra_fields)
        local_extra_fields.update(kwargs)

        extra_fields_message = self.__dict_to_string(local_extra_fields)
        log_message = f'{message} | {extra_fields_message}' if extra_fields_message != '' else message

        if self.logger_level != "OFF":

            if logger_level == logging.CRITICAL:
                self.logger.critical(log_message)
            elif logger_level == logging.ERROR:
                self.logger.error(log_message)
            elif logger_level == logging.WARNING:
                self.logger.warning(log_message)
            elif logger_level == logging.INFO:
                self.logger.info(log_message)
            elif logger_level == logging.DEBUG:
                self.logger.debug(log_message)

    def __dict_to_string(self, dictionary):
        return ' | '.join([f'{key} = {value}' for key, value in dictionary.items()])