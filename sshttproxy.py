#!/usr/bin/python
import argparse
import re
import traceback
from collections import defaultdict
import eventlet
from eventlet.green import select
paramiko = eventlet.import_patched('paramiko')

ssh_client_locks = defaultdict(eventlet.semaphore.BoundedSemaphore)
ssh_clients = {}
def get_ssh_client(hostname):
	"""Create SSHClient for hostname or return pre-existing client."""
	with ssh_client_locks[hostname]:
		if hostname not in ssh_clients:
			client = paramiko.SSHClient()
			client.load_system_host_keys()
			client.connect(hostname)
			ssh_clients[hostname] = client
	return ssh_clients[hostname]

def create_tunnel(local_conn, remote_host, remote_port):
	"""Create tunnel for forwarding."""
	transport = get_ssh_client(remote_host).get_transport()
	channel = transport.open_channel('direct-tcpip',
		('localhost', remote_port),
		local_conn.getpeername())
	if not channel:
		raise Exception('Remote host %s refused connection on %s' 
			% (remote_host, remote_port))
	return channel

def forward(conn_a, conn_b):
	"""Forward data both ways between connections until one closes."""
	conns = conn_a, conn_b
	while True:
		# Get connections that are ready to read from
		for conn in select.select(conns, [], [])[0]:
			data = conn.recv(32768)
			if len(data) == 0:
				return
			# Write data to the other connection
			conns[1-conns.index(conn)].sendall(data)

def http_error(text):
	"""Create HTTP error response."""
	return (
		'HTTP/1.0 500  Internal Server Error\r\n'
		'Content-Length: %d\r\n'
		'Content-Type: text/plain\r\n'
		'\r\n%s' %
			(len(text), text))

def extract_remote_host_port(http_data):
	"""
	Extract tunnel requirements from HTTP Host header.
	
	Rightmost all-numeric subdomain is treated as the remote port,
	everything to the left is treated as the remote host e.g:
	
		remote-host.example.com.8080.forward.localhost
		
	connects to remote-host.example.com on port 8080.
	"""
	host_header = re.search(r'^Host:\s+(\S+)(\s|$)', http_data,
		re.I | re.M).group(1)
	match = re.search(r'^(?P<host>.+)\.(?P<port>\d+)\.', host_header)
	return match.group('host'), int(match.group('port'))

def connect_to_remote_host(client):
	"""Extract remote host details, create tunnel and forward traffic."""
	# Grab the first chunk of client data
	data = client.recv(1024)
	try:
		remote_host, remote_port = extract_remote_host_port(data)
		server = create_tunnel(client, remote_host, remote_port)
	except Exception, e:
		client.sendall(http_error('Connection failure:\n%s'
			% traceback.format_exc()))
		client.close()
		return
	
	# Send initial chunk to server
	server.sendall(data)
	# Forward data both ways until one connection closes
	forward(client, server)
	client.close()
	server.close()

def listen(address):
	"""Listen for incoming connections and forward to remote hosts"""
	listener = eventlet.listen(address)
	while True:
		client = listener.accept()[0]
		eventlet.spawn_n(connect_to_remote_host, client)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--port', '-p', type=int, default=7150,
		help='port to listen on')
	parser.add_argument('--host', default='localhost',
		help='host to listen on')
	args = parser.parse_args()
	
	listen((args.host, args.port))

