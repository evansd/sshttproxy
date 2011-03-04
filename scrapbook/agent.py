import eventlet
from eventlet.green import select, socket

def forward(source, dest):
	"""Forwards bytes unidirectionally from source to dest"""
	while True:
		d = source.recv(32384)
		if d == '':
			dest.shutdown(2)
			dest.close()
			print 'closed'
			break
		dest.sendall(d)

def forward_response(client):
	while True:
		server = eventlet.connect(('localhost', 80))
		while True:
			d = server.recv(32384)
			if d == '':
				break
			client.sendall(d)

def wait_for_host(source):
	print 'waiting'
	d = source.recv(512)
	print 'got stuff'
	host = [l for l in d.splitlines() if l.startswith('Host:')][0].partition('Host:')[2].strip()
	print host
	server = eventlet.connect(('localhost', 80))
	# two unidirectional forwarders make a bidirectional one
	eventlet.spawn_n(forward_response, client, server)
	# Forward response from server
	eventlet.spawn_n(forward_response, server, client)
	server.sendall(d)

def proxy(client):
	data = client.recv(1024*1024)
	server = eventlet.connect(('localhost', 80))
	server.sendall(data)
	data = server.recv(1024*1024)
	client.sendall(data)
	server.close()
	client.close()

def is_active(sock):
	return True
	sel = select.select([client],[client],[client], 0)
	print sel
	return sel == ([], [], [])

listener = eventlet.listen(('localhost', 7000))
while True:
	client, addr = listener.accept()
	eventlet.spawn_n(proxy, client)
