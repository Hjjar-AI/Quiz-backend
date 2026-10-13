"""Keep development-server socket failures separate from application errors."""

import errno
import logging
import socket
import sys
import socketserver
from wsgiref.handlers import SimpleHandler

from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticFilesRunserverCommand,
)
from django.core.servers.basehttp import ServerHandler, WSGIRequestHandler, WSGIServer


logger = logging.getLogger("django.server")


class DevelopmentServerHandler(ServerHandler):
    def handle_error(self):
        _, error, traceback = sys.exc_info()
        previous = None
        iterable_already_closed = False
        while traceback is not None and traceback.tb_next is not None:
            if traceback.tb_frame.f_code is SimpleHandler.finish_response.__code__:
                iterable_already_closed = True
            previous = traceback
            traceback = traceback.tb_next
        if (
            isinstance(error, TimeoutError)
            and error.errno == errno.ETIMEDOUT
            and previous is not None
            and previous.tb_frame.f_code is SimpleHandler._write.__code__
            and traceback.tb_frame.f_code is socketserver._SocketWriter.write.__code__
        ):
            # The response may follow a committed write. Close the failed
            # response/connection; never replay the application or send a 500
            # down the same broken socket. Other exceptions retain diagnostics.
            self.request_handler.close_connection = True
            logger.info("- Client connection ended while sending response (errno=%s)", error.errno)
            # Close the response iterable without Django's unread-body drain,
            # which could block again on the already failed connection.
            if iterable_already_closed:
                # WSGI finish_response already closed it while unwinding.
                self.result = None
            SimpleHandler.close(self)
            return
        super().handle_error()


class DevelopmentRequestHandler(WSGIRequestHandler):
    def handle_one_request(self):
        # Match the installed Django request lifecycle, substituting only the
        # response handler. Keep HTTP parsing, 414, environ and static serving.
        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ""
            self.request_version = ""
            self.command = ""
            self.send_error(414)
            return
        if not self.parse_request():
            return
        handler = DevelopmentServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ(),
        )
        handler.request_handler = self
        handler.run(self.server.get_app())


class DevelopmentWSGIServer(WSGIServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.RequestHandlerClass = DevelopmentRequestHandler

    def get_request(self):
        connection, address = super().get_request()
        try:
            # A vanished mobile/NAT/network path otherwise leaves a request
            # thread blocked indefinitely. Probe idle TCP connections without
            # imposing a deadline on uploads, exports or application work.
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            for name, value in (
                ("TCP_KEEPIDLE", 60),
                ("TCP_KEEPINTVL", 20),
                ("TCP_KEEPCNT", 3),
            ):
                option = getattr(socket, name, None)
                if option is not None:
                    try:
                        connection.setsockopt(socket.IPPROTO_TCP, option, value)
                    except OSError:
                        # Platforms may expose an option their kernel does
                        # not support. Keep the portable SO_KEEPALIVE setting.
                        logger.debug("TCP keepalive tuning unavailable: %s", name)
        except OSError:
            connection.close()
            raise
        return connection, address

    def handle_error(self, request, client_address):
        _, error, traceback = sys.exc_info()
        if isinstance(error, OSError) and error.errno in (
            errno.ECONNREFUSED, errno.ETIMEDOUT, errno.ENETUNREACH,
        ):
            # Match the supplied failure at rfile.readline(), including reads
            # of the next request on a persistent connection. Never suppress
            # connection errors raised by application/dependency code.
            previous = None
            while traceback is not None and traceback.tb_next is not None:
                previous = traceback
                traceback = traceback.tb_next
            if (
                previous is not None
                and previous.tb_frame.f_code in (
                    WSGIRequestHandler.handle_one_request.__code__,
                    DevelopmentRequestHandler.handle_one_request.__code__,
                )
                and traceback.tb_frame.f_code is socket.SocketIO.readinto.__code__
            ):
                logger.info(
                    "- Client connection ended while reading request line from %s (errno=%s)",
                    client_address, error.errno,
                )
                return
        super().handle_error(request, client_address)


class Command(StaticFilesRunserverCommand):
    # Retain Django's static serving, CLI flags, reload and threaded/nonthreaded
    # lifecycle. Both start.py launchers and manage.py discover this command.
    server_cls = DevelopmentWSGIServer
