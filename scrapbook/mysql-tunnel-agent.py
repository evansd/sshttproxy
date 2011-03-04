import socket, os, subprocess

tunnels = {}

def get_port_for_tunnel(hostname):
	if hostname in tunnels:
		port = tunnels[hostname][0]
	else:
		port = get_free_local_port()
		process = subprocess.Popen(['ssh', hostname, '-N', '-L', '%d:localhost:3306' % port], close_fds=True)
		tunnels[hostname] = (port, process)
	return (port, None)

def get_free_local_port():
	# Hacky implementation: bind to port 0 and see which port the system
	# gives us, then close the socket.
	sock = socket.socket()
	sock.bind(('localhost', 0))
	port = sock.getsockname()[1]
	sock.close()
	return port

def request_handler(req):
	hostname = req.strip()
	port, err = get_port_for_tunnel(hostname)
	if port:
		return 'OK:%d' % port
	else:
		return 'ERROR:%s' % err

def crude_socket_server(sock_path, handler):
	if os.path.exists(sock_path):
		os.remove(sock_path)
	server = socket.socket(socket.AF_UNIX)
	server.bind(sock_path)
	os.chmod(sock_path, 0666)
	try:
		server.listen(1)
		while True:
			conn, addr = server.accept()
			req = conn.recv(1024)
			resp = handler(req)
			if resp:
				conn.send(resp)
			conn.close()
	finally:
		server.close()
		if os.path.exists(sock_path):
			os.remove(sock_path)
		
crude_socket_server('/tmp/mysql_tunnel_agent.sock', request_handler)
