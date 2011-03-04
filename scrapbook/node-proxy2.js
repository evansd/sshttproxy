var net = require('net'),
    spawn = require('child_process').spawn;

var tunnels = {};

function get_or_create_tunnel(hostname, remote_port, callback) {
    var key = hostname + ':' + remote_port;
    
    if (tunnels[key]) {
        if (tunnels[key] !== 'locked') {
            callback(tunnels[key]);
        } else {
            setTimeout(get_or_create_tunnel, 100, hostname, remote_port, callback);
        }
    } else {
        tunnels[key] = 'locked';
        get_free_local_port(function(local_port) {
             spawn('ssh', [hostname, '-N', '-L', local_port+':localhost:'+remote_port]);
             tunnels[key] = local_port;
             setTimeout(callback, 1500, local_port);
        });
    }
}

function get_free_local_port(callback) {
    var server = net.createServer();
    server.listen(0, 'localhost', null, function() {
        var port = server.address().port;
        server.on('close', function() {
            callback(port);
        });
        server.close();
    });
}

var server = net.createServer(function(stream) {
	stream.on('connect', function() {
        
		var client = false;

		stream.on('data', function(data) {
            if (client) {
                client.write(data);
            } else {
                var matches = data.toString('ascii').match(/^Host:\s*(.+?)\.p(\d+)\.localhost(:\d+)?$/mi);
    
                if ( ! matches) {
                    stream.write(new Buffer('HTTP/1.0 200 OK\nContent-Length: 10\nContent-Type: text/plain\n\nError Fail'));
                    stream.end();
                    return false;
                }
                
                get_or_create_tunnel(matches[1], matches[2], function(local_port) {
                    client = net.createConnection(local_port);
                    
                    client.write(data);
                    
                    client.on('data', function(data) {
                        stream.write(data);
                    });

                    client.on('end', function() {
                        client.end();
                        stream.end();
                        client = false;
                    });
                });
               
            }
		});

		stream.on('end', function() {
			stream.end();
			if (client) client.end();
		});
	});
});

server.listen(7010, 'localhost')

