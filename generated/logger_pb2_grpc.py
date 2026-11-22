# -*- coding: utf-8 -*-
import grpc
from generated import logger_pb2

class LoggerServiceStub(object):
    def __init__(self, channel):
        self.LogHit = channel.unary_unary(
            '/logger.LoggerService/LogHit',
            request_serializer=logger_pb2.HitRequest.SerializeToString,
            response_deserializer=logger_pb2.HitResponse.FromString,
        )

class LoggerServiceServicer(object):
    def LogHit(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_LoggerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'LogHit': grpc.unary_unary_rpc_method_handler(
            servicer.LogHit,
            request_deserializer=logger_pb2.HitRequest.FromString,
            response_serializer=logger_pb2.HitResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'logger.LoggerService', rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))
