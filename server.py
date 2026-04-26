import flwr as fl
fl.server.start_server(
    server_address='0.0.0.0:9091',
    config=fl.server.ServerConfig(num_rounds=100)
)