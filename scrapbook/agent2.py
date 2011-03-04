import eventlet

def forward(source, dest, conn_type):
	"""Forwards bytes unidirectionally from source to dest"""
	print 'connected: ', conn_type
	while True:
		d = source['sock'].recv(32384)
		print 'data from:', conn_type
		if d == '':
			break
		dest['sock'].send(d)

listener = eventlet.listen(('localhost', 7000))
while True:
	client, addr = listener.accept()
	server = eventlet.connect(('localhost', 80))
	# two unidirectional forwarders make a bidirectional one
	client = {'sock': client, 'open': 1}
	server = {'sock': server, 'open': 1}
	eventlet.spawn_n(forward, client, server, 'client')
	eventlet.spawn_n(forward, server, client, 'server')
