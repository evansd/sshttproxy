import eventlet
from eventlet.green import select, socket, subprocess
import re

tunnels = {}

def get_port_for_tunnel(hostname, remote_port):
	key = (hostname, remote_port)
	if key in tunnels:
		local_port = tunnels[key][0]
	else:
		local_port = get_free_local_port()
		process = subprocess.Popen(['ssh', hostname, '-N', '-L', '%d:localhost:%d' % (local_port, remote_port)], close_fds=True)
		eventlet.sleep(1)
		tunnels[key] = (local_port, process)
	return (local_port, None)

def get_free_local_port():
	# Hacky implementation: bind to port 0 and see which port the system
	# gives us, then close the socket.
	sock = socket.socket()
	sock.bind(('localhost', 0))
	port = sock.getsockname()[1]
	sock.close()
	return port

def tunnel(client, server):
	while True:
		read_ready = select.select([client, server], [], [])[0]
		if client in read_ready:
			data = client.recv(1024)
			if len(data) == 0:
				break
			server.sendall(data)
		if server in read_ready:
			data = server.recv(1024)
			if len(data) == 0:
				break
			client.sendall(data)
	server.close()
	client.close()

def connect_to_remote_host(client):
	data = client.recv(1024)
	
	remote_port = None
	
	host = re.search(r'^Host:\s+(.+)$', data, re.IGNORECASE | re.MULTILINE)
	if host:
		match = re.search(r'^((.+)\.p(\d+)\.localhost)(:\d+)?$', host.group(1).strip())
		if match:
			hostname, remote_port = match.group(2), int(match.group(3))
	
	if not remote_port:
		client.sendall('HTTP/1.0 200 OK\nContent-Length: 10\nContent-Type: text/plain\n\nError Fail')
		client.close()
		return
	
	local_port, err = get_port_for_tunnel(hostname, remote_port)
	
	server = eventlet.connect(('localhost', local_port))
	server.sendall(data)
	tunnel(client, server)

listener = eventlet.listen(('localhost', 7000))
while True:
	client, addr = listener.accept()
	eventlet.spawn_n(connect_to_remote_host, client)

