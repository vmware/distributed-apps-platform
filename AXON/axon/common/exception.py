import logging
import six


LOG = logging.getLogger(__name__)


class AxonException(Exception):
    """Base Axon Exception
    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = ("An unknown exception occurred.")

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs
        if message:
            self.message = message

        try:
            self.message = str(self.message) % kwargs
        except KeyError:
            # kwargs doesn't match a variable in the message
            # log the issue and the kwargs
            LOG.exception('Exception in string format operation, '
                          'kwargs: %s', kwargs)
        super(AxonException, self).__init__(self.message)

    def __str__(self):
        if six.PY3:
            return self.message
        return self.message.encode('utf-8')

    def __unicode__(self):
        return self.message

    def format_message(self):
        return six.text_type(self)


# SQL Database Errors
class SqlDbException(AxonException):
    message = ('Database Exception happened : %(reason)s')


class WebFrontException(AxonException):
    message = ('WebFront Exception happened : %(reason)s')


class ServerOperationException(AxonException):
    message = ('Failed to %(action)s on port %(port)s and protocol %(proto)s')
