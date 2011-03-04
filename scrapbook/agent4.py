import eventlet
from eventlet.green import select, socket

def forward(source, dest):
	"""Forwards bytes unidirectionally from source to dest"""
	while True:
		d = source.recv(32384)
		if d == '':
			dest.close()
			print source.getsockname(), 'closed'
			source.close()
			break
		dest.sendall(d)

listener = eventlet.listen(('localhost', 7000))
while True:
	client, addr = listener.accept()
	server = eventlet.connect(('localhost', 80))
	eventlet.spawn_n(forward, client, server)
	eventlet.spawn_n(forward, server, client)
