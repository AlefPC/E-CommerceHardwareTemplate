from application import app
from threading import Thread
from werkzeug.serving import make_server

if __name__ == "__main__":
    ports = (4000, 4001, 4002, 4003, 4004)
    servers = [
        make_server("127.0.0.1", port, app, threaded=True)
        for port in ports
    ]
    threads = [
        Thread(target=server.serve_forever)
        for server in servers
    ]

    for thread in threads:
        thread.start()

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.shutdown()
