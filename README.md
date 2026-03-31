# Video-Game-Exchange-API
A distributed system for managing video games (adding, removing, updating, deleting, and exchanging with other users) and users 
using fastapi in python.

# Distributed Components
Nginx - Reverse proxy API gateway / round-robin load balancing
Redis - Temporary cache of API responses
Mongo - DB store for trades and user data
Kafka - Asynchronous event queue used to asynchronously publish email notification events
Grafana - Dashboard visualization tool for our prometheus metrics
Prometheus - Distributed metric puller

