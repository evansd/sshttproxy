var http = require('http');

http.createServer(function(request, response) {
	var proxy = http.createClient(46595, 'localhost')
	var proxy_request = proxy.request(request.method, request.url, request.headers);
	proxy_request.addListener('response', function (proxy_response) {
		proxy_response.addListener('data', function(chunk) {
			response.write(chunk, 'binary');
		});
		proxy_response.addListener('end', function() {
			response.end();
		});
		console.log(proxy_response.headers);
		response.writeHead(proxy_response.statusCode, proxy_response.headers);
	});
	request.addListener('data', function(chunk) {
		proxy_request.write(chunk, 'binary');
	});
	request.addListener('end', function() {
		proxy_request.end();
	});
}).listen(7010);
