#/usr/bin/python

# For handling requests
import cgi
import BaseHTTPServer

# For creating scheme interpreters
import subprocess

# For setting blocking IO with timeouts
import signal

# For setting interpreter_process.stdout O_NOBLOCK
import os
import fcntl

# Because in the end I just gave up :(
import time

# TODO: create a...process? for each interpreter
# and use *signal.signal* in it to communicate with scheme

# TODO: impose time/memory limits on computations

# TODO: AJAX (jquery)

# TODO: Write this in pure C?


SCHEME_INTERPRETER = "guile"
scheme_interpreters = {}

def spawn_new_interpreter(address):
    # Spawn the new process
    proc = subprocess.Popen(
        SCHEME_INTERPRETER,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    # Set stdout and stderr to not block
    fd = proc.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    fd = proc.stderr.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    scheme_interpreters[address] = proc
    print "Created Interpreter"

# TODO: Reserved for better days.
'''
class IOTimeout(Exception):
    pass

def alarm_handler(*args):
      """ This signal stuff may not work in non unix env """
      raise IOTimeout

signal.signal(signal.SIGALRM, alarm_handler)
'''

def write_data(address, source):
    scheme_interpreters[address].stdin.write(source)
    # flush data
    scheme_interpreters[address].stdin.write("\n")
    # FIXME: What was I thinking?
    '''
    scheme_interpreters[address].stdin.flush()
    #(+ 2 3)
    print(scheme_interpreters[address].stdin.fileno())
    #os.fsync()
    '''

def read_data(address):
    out = []
    err = []
    try:
        while True:
            line = scheme_interpreters[address].stdout.readline()
            out.append(line)
            print "ala"
    #except IOTimeout:
    except IOError:
        print "ERROR out"
        pass

    try:
        while True:
            line = scheme_interpreters[address].stderr.readline()
            stderr.append(line)
    except IOError, e:
        print "ERROR err"
        pass
    

    try:
        while True:
            line = scheme_interpreters[address].stderr.readline()
            err.append(line)
    except IOError, e:
        pass
        #print e
    return out,err


class Schemer(BaseHTTPServer.BaseHTTPRequestHandler):
    def default_headers(self):
        self.send_response(200)
        self.send_header('Content-type',    'text/html')
        self.end_headers()

    def do_GET(self):
        '''
        Only the first request is "get".
        It just loads an empty page with a textarea.
        '''
        try:
            print "GET Received"
            self.default_headers()

            self.wfile.write(open("test.html").read())
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

    def do_POST(self):
        '''
        This happens every time data is sent to the server.
        Right now it reloads the page and set values inside it.

        At some point in the future, this will turn into an AJAX call,
        which only sends the new results to the client.
        '''
        try:
            print "POST Received"
            self.default_headers()

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype != 'multipart/form-data':
                self.send_error(404, "File not found!")
                return

            query=cgi.parse_multipart(self.rfile, pdict)
            source = query.get("source")[0]

            address = self.client_address[0]
            if address not in scheme_interpreters:
                spawn_new_interpreter(address)

            write_data(address, source)

            # Humongously bad race condition.
            # No, really.
            # Just come and confiscate my star-wars toys.
            # I'm obviously no real geek.
            # NOTE: I even forgot to "import time" the first time this was run.
            # So, yeah, double fail.
            time.sleep(0.2)
            out, err = read_data(address)
            print(out, err)

            text = open("test.html").read()
            text = text % {"out": str(out), "err": str(err)}
            self.wfile.write(text)
        except Exception, e:
            print "Error:", e
            raise


def main():
    try:
        server = BaseHTTPServer.HTTPServer(('', 8080), Schemer)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
    finally:
        print "Exiting!"
        for name, interpreter in scheme_interpreters.items():
            print "Stopping interpreter from %s" % name
            interpreter.kill()

if __name__ == '__main__':
    main()
