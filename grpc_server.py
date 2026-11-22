from concurrent import futures
import grpc
import sys
import os

sys.path.append(os.path.dirname(__file__))

from generated import logger_pb2, logger_pb2_grpc
from db_logger import init_log_db, insert_hit

class LoggerServiceServicer(logger_pb2_grpc.LoggerServiceServicer):
    def LogHit(self, request, context):
        print(f"[gRPC Log Server] Evento recibido: URL={request.url} en {request.timestamp}")
        insert_hit(request.timestamp, request.url)
        return logger_pb2.HitResponse(success=True)

def serve():
    init_log_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    logger_pb2_grpc.add_LoggerServiceServicer_to_server(LoggerServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    print("Servidor gRPC iniciado en puerto 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()