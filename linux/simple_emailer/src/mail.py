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
CMD_AUTH = b'AUTH'
CMD_MAIL = b'MAIL'
AUTH_PLAIN = b'PLAIN'
AUTH_LOGIN = b'LOGIN'

def readline(sock):
    print("readline called")
    line = b""
    while True:
        b = sock.read(1)
        if b == b"\n":
            break
        #print("readline read", b)
        line = line + b
    print("readline returning", line)
    return line
    

class SMTP:
    def cmd(self,cmd_str):
        print("cmd called", cmd_str)
        try:
            sock = self._sock;
            try:
                cmd = '%s\r\n' % cmd_str
                sock.write(bytes(cmd, 'utf-8'))
            except Exception as e:
                    print("cmd first cmd write failed", e)
            resp = []
            next = True
            try:
                while next:
                    code = sock.read(3)
                    next = sock.read(1) == b'-'
                    #resp.append(readline(sock).strip().decode())
                    resp.append(readline(sock).strip())
            except Exception as e:
                    print("cmd resp.append failed", e)
            print("cmd returning", code, resp) 
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
        if code!=220:
            print ('cant connect to server', code)
            raise
        self._sock = sock
        print("saved _sock")
        try:
            code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
        except Exception as e:
                print("self.cmd( failed", e)
        print("code, resp = self.cmd returned", code,resp)
        assert code==250, '%d' % code
        if not ssl and CMD_STARTTLS in resp:
            code, resp = self.cmd(CMD_STARTTLS)
            assert code==220, 'start tls failed %d, %s' % (code, resp)
            self._sock = ssl.wrap_socket(sock)

        if username and password:
            self.login(username, password)

    def login(self, username, password):
        print("login starting")
        self.username = username
        code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
        if code!=250:
            print("login CMD_EHLO failed", code)
            assert "login CMD_EHLO failed"

        auths = None
        for feature in resp:
            print("looking for CMD_AUTHs", feature)
            if feature[:4].upper() == CMD_AUTH:
                auths = feature[4:].strip(b'=').upper().split()
        assert auths!=None, "no auth method"

        from binascii import b2a_base64 as b64
        if AUTH_PLAIN in auths:
            print("found AUTH_PLAIN")
            user_password = ("\0%s\0%s" % (username, password)).encode("utf-8")
            print("login user_password", user_password)
            cren = b64(user_password)[:-1].decode()
            print("login cren", cren)
            
            code, resp = self.cmd(('%s %s %s' % (CMD_AUTH.decode('utf-8'),AUTH_PLAIN.decode('utf-8'), cren)))
            print("AUTH_PLAIN done", code, resp)
        elif AUTH_LOGIN in auths:
            print("found AUTH_LOGIN")
            code, resp = self.cmd("%s %s %s" % (CMD_AUTH.decode('utf-8'), AUTH_LOGIN.decode('utf-8'), b64(username)[:-1].decode()))
            assert code==334, 'wrong username %d, %s' % (code, resp)
            code, resp = self.cmd(b64(password)[:-1].decode())
        else:
            raise Exception("auth(%s) not supported " % ', '.join(auths))

        assert code==235 or code==503, 'login auth error %d, %s' % (code, resp)
        print("login returning")
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
        print("write type of", content, type(content))
        if type(content) is str: 
            self._sock.write(content.encode("utf-8")) 
        else:    
            self._sock.write(content)

    def send(self, content=b''):
        if content:
            self.write(content)
        self._sock.write(b'\r\n.\r\n') # the five letter sequence marked for ending
        line = readline(self._sock)
        return (int(line[:3]), line[4:].strip().decode())

    def quit(self):
        self.cmd(b"QUIT")
        self._sock.close()
