# mail - simple mail for non micropython built from uMail Jim dodgen 2025 MIT licence
# uMail (MicroMail) for MicroPython
# Copyright (c) 2018 Shawwwn <shawwwn1@gmail.com>
# License: MIT
#
import socket

xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[mail]", *args, **kwargs) # the copied real print

DEFAULT_TIMEOUT = 10 # sec
LOCAL_DOMAIN = '127.0.0.1'
CMD_EHLO = 'EHLO'
CMD_STARTTLS = 'STARTTLS'
CMD_AUTH = 'AUTH'
CMD_MAIL = 'MAIL'
AUTH_PLAIN = 'PLAIN'
AUTH_LOGIN = 'LOGIN'

def readline(sock):
    line = ""
    while True:
        b = sock.read(1)
        if b == b"\n":
            break
        line += chr(b)
    return line
    

class SMTP:
    def cmd(self, cmd_str):
        try:
            sock = self._sock;
            try:
                cmd = '%s\r\n' % cmd_str
                sock.write(bytes(cmd, 'utf-8'))
            except Exception as e:
                    print("first write failed", e)
            resp = []
            next = True
            try:
                while next:
                    code = sock.read(3)
                    next = sock.read(1) == b'-'
                    resp.append(readline(sock).strip().decode())
            except Exception as e:
                    print("resp.append", e)
            print("smtp", code) 
            return int(code.decode('utf-8')), resp
        except Exception as e:
            print("cmd failed", e)

    def __init__(self, host, port, ssl=False, username=None, password=None):
        import ssl
        self.username = username
        addr = socket.getaddrinfo(host, port)[0][-1]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(DEFAULT_TIMEOUT)
        sock.connect(addr)
        if ssl:
            sock = ssl.wrap_socket(sock)
        raw=sock.read(3) 
        print("raw", raw)   
        code = int(raw.decode('utf-8'))
        print("code", code)
        readline(sock)
        assert code==220, 'cant connect to server %d, %s' % (code, resp)
        self._sock = sock
        try:
            code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
        except Exception as e:
                print("self.cmd(", e)
        print("code, resp = self.cmd", code)
        assert code==250, '%d' % code
        if not ssl and CMD_STARTTLS in resp:
            code, resp = self.cmd(CMD_STARTTLS)
            assert code==220, 'start tls failed %d, %s' % (code, resp)
            self._sock = ssl.wrap_socket(sock)

        if username and password:
            self.login(username, password)

    def login(self, username, password):
        self.username = username
        code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
        assert code==250, '%d, %s' % (code, resp)

        auths = None
        for feature in resp:
            if feature[:4].upper() == CMD_AUTH:
                auths = feature[4:].strip('=').upper().split()
        assert auths!=None, "no auth method"

        from ubinascii import b2a_base64 as b64
        if AUTH_PLAIN in auths:
            cren = b64("\0%s\0%s" % (username, password))[:-1].decode()
            code, resp = self.cmd('%s %s %s' % (CMD_AUTH, AUTH_PLAIN, cren))
        elif AUTH_LOGIN in auths:
            code, resp = self.cmd("%s %s %s" % (CMD_AUTH, AUTH_LOGIN, b64(username)[:-1].decode()))
            assert code==334, 'wrong username %d, %s' % (code, resp)
            code, resp = self.cmd(b64(password)[:-1].decode())
        else:
            raise Exception("auth(%s) not supported " % ', '.join(auths))

        assert code==235 or code==503, 'auth error %d, %s' % (code, resp)
        return code, resp

    def to(self, addrs, mail_from=None):
        mail_from = self.username if mail_from==None else mail_from
        code, resp = self.cmd('MAIL FROM: <%s>' % mail_from)
        assert code==250, 'sender refused %d, %s' % (code, resp)

        if isinstance(addrs, str):
            addrs = [addrs]
        count = 0
        for addr in addrs:
            code, resp = self.cmd('RCPT TO: <%s>' % addr)
            if code!=250 and code!=251:
                print('%s refused, %s' % (addr, resp))
                count += 1
        assert count!=len(addrs), 'recipient refused, %d, %s' % (code, resp)

        code, resp = self.cmd('DATA')
        assert code==354, 'data refused, %d, %s' % (code, resp)
        return code, resp

    def write(self, content):
        self._sock.write(content)

    def send(self, content=''):
        if content:
            self.write(content)
        self._sock.write('\r\n.\r\n') # the five letter sequence marked for ending
        line = self._sock.readline()
        return (int(line[:3]), line[4:].strip().decode())

    def quit(self):
        self.cmd("QUIT")
        self._sock.close()
