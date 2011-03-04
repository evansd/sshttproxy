import eventlet
from eventlet import wsgi
from eventlet.green import httplib, urllib, socket, subprocess
import re
from pprint import pprint

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

def proxy(env, start_response):
	
	headers = {}
	for key, value in env.items():
		if key.startswith('HTTP_'):
			key = key[5:].lower().replace('_', '-')
			headers[key] = value
	
	match = re.search(r'^((.+)\.p(\d+)\.localhost)(:\d+)?$', headers['host']) 
	pprint(env)
	if match:
		port, err = get_port_for_tunnel(match.group(2), int(match.group(3)))
		print port
		#headers['host'] = match.group(2)
	else:
		start_response('400 Bad Request', [('Content-Type', 'text/plain')])
		return ['Errors etc.']
	
	print 'opening connection'
	conn = httplib.HTTPConnection('localhost', port)
	
	if env.get('CONTENT_TYPE'):
		headers['content-type'] = env['CONTENT_TYPE']
	
	print 'reading body'
	if env.get('CONTENT_LENGTH'):
		if env['CONTENT_LENGTH'] == '-1':
			# This is a special case, where the content length is basically undetermined
			body = env['eventlet.input'].read(-1)
			headers['content-length'] = str(len(body))
		else:
			headers['content-length'] = env['CONTENT_LENGTH'] 
			length = int(env['CONTENT_LENGTH'])
			body = env['eventlet.input'].read(length)
	else:
		body = ''
	print 'read body', body
	
	print 'starting remote request'
	conn.request(env['REQUEST_METHOD'], original_url(env), body, headers)
	print 'getting response'
	resp = conn.getresponse()
	resp_headers = [(k,v) for (k,v) in resp.getheaders() if k != 'transfer-encoding' and k!= 'connection']
	pprint(resp_headers)
	
	start_response('%s %s' % (resp.status, resp.reason), resp_headers)
	
	data = resp.read()
	conn.close()
	print 'returning iterator'
	#return response_iterator(conn, resp)
	return [data]

def response_iterator(connection, response, size=1024):
		while True:
			data = response.read(size)
			if data == '':
				break
			yield data
		connection.close()

def original_url(environ):
	return ''.join([
		urllib.quote(environ.get('SCRIPT_NAME', '')),
		urllib.quote(environ.get('PATH_INFO', '')),
		'?' if 'QUERY_STRING' in environ else '',
		environ.get('QUERY_STRING', '')
	])

wsgi.server(eventlet.listen(('localhost', 7000)), proxy)
