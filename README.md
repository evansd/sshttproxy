# sshttproxy: a connect-on-demand SSH HTTP Proxy
<small>(You have my permission to pronounce it _sh*t proxy_, if you wish)</small>

sshttproxy parses the Host header of incoming HTTP requests, works out which remote host and port they are destined for, creates an SSH tunnel to that host and forwards the request. For example, requests for <tt>http://example.com.8080.localhost</tt> will get forwarded to port 8080 on <tt>example.com</tt>.


## Why?

I wanted a hassle free way of securing access to web-based administration tools (e.g., phpMyAdmin) on remote servers. Having these apps listen only on localhost and then tunnelling a port over SSH provided a good level of security, but it was a pain to have to keep setting up the tunnels and not having consistent local URLs meant I couldn't use my password manager to store login information. Now all I need to do is bookmark a URL.


## Usage

Start it up on some local port:

    ./sshttproxy.py
    usage: sshttproxy.py [-h] [--port PORT] [--host HOST]

    optional arguments:
      -h, --help            show this help message and exit
      --port PORT, -p PORT  port to listen on (default: 7150)
      --host HOST           host to listen on (default: localhost)

Connect to your favourite server:

    http://remote-host.example.com.8080.whatever.localhost:7150/

Host headers are parsed as follows:

 * the rightmost all-numeric subdomain is treated as the remote port;
 * everything to the left of this is treated as the remote hostname;
 * everything to the right is ignored.


## Dependencies

I've only tested this on Python 2.6.

It uses two third-party Python modules: [paramiko](http://www.lag.net/paramiko/) which handles the SSH stuff and [eventlet](http://eventlet.net) which provides networking concurrency.


## Notes

**This won't be much use unless you can resolve arbitrary subdomains of localhost.**<br />
Obviously you could add entries to <tt>/etc/hosts</tt> every time but it kind of defeats the purpose of creating tunnels with zero configuration. Fortunately, it's easy to set this up: just use [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html). (See also my [brief guide](http://drhevans.com/blog/posts/106-wildcard-subdomains-of-localhost) to configuring dnsmasq.) It's a handy feature to have anyway for development purposes.

**The app you're connecting to must be Host header agnostic.**<br />
sshttproxy passes your entire request through untouched (it's a TCP-level proxy really) so the web app on the other end needs to not mind that the Host header ends in <tt>.localhost</tt>. This means, among other things, that virtual hosting won't work, so the app needs to be the only thing listening on that particular port. This shouldn't be too difficult to satisfy though, given that you can choose any arbitrary port with no firewalls to worry about.

**Make sure the SSH keys you need are loaded into your key agent.**<br />
sshttproxy makes no attempt to prompt you for your password or to load keys.

**Make sure the host is in your <tt>known_hosts</tt> list.**<br />
For simplicty and safety's sake, sshttproxy refuses to connect to any hosts it doesn't recognise.

