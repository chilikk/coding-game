import socket, random, sys, math, os, copy, select, string

############# one-threaded, so only one task at a time :(

def main(levelmap):
    lsocks = []
    callmap = dict()
    try:
        for port in levelmap:
            lsock = socket.socket()
            lsocks.append(lsock)
            callmap[lsock] = levelmap[port]
            lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            lsock.bind(("0.0.0.0",port))
            lsock.listen(1)
        while True:
            ready = select.select(lsocks, [], [])
            if ready[0]:
                lsock = ready[0][0]
                (sock, remote) = lsock.accept()
                print "New client connected from %s:%s" % remote
                sys.stdout.flush()
                try:
                    levelfun = callmap[lsock]
                    levelfun(sock, remote)
                except Exception as e:
                    print "An exception occured: %s" % e
                    sys.stdout.flush()
                    try:
                        sock.send("You did something really wrong :(\n")
                    except:
                        pass
                finally:
                    print "Closing connection with remote"
                    sys.stdout.flush()
                    try:
                        sock.close()
                    except:
                        pass
    finally:
        map(lambda x : x.close(), lsocks)

########### individual levels

def arithmetic():
    a = random.randint(0, 100000)
    sign = random.choice(["+", "-", "*", "/"])
    if sign == '+':
        b = random.randint(0, 100000)
        correct = a + b
    elif sign == '-':
        b = random.randint(0, a)
        correct = a - b
    elif sign == '*':
        b = random.randint(1, 100000)
        correct = a * b
    elif sign == '/':
        b = random.randint(1, math.floor(math.sqrt(a)))
        correct = a / b
        a = b * correct
    question = "%d %s %d" % (a, sign, b)
    return (question, correct)

def level1(sock, remote):
    random.seed()
    ok = True
    i = 0
    while ok and i < 1000:
        i += 1
        (tosend, correct) = arithmetic()
        tosend += " = "
        sock.send(tosend)
        ready = select.select([sock], [], [], 5)
        if ready[0]:
            result = sock.recv(1024)
            intresult = int(result.strip())
            print "%s%d" % (tosend, intresult)
            sys.stdout.flush()
            if not intresult == correct:
                say(sock, "wrong. too bad :(")
                ok = False
        else:
            say(sock, "you have to respond quicker, try again")
            ok = False
    if ok:
        say(sock, "YAAAY! next level port 9001")
    return ok

def level2(sock, remote):
    say(sock, "I will tell you who knows whom. " \
              "Keep in mind that if Alice knows Bob, " \
              "that doesn't mean that Bob knows Alice, " \
              "unless stated otherwise. In the end you " \
              "will have to answer my question. " \
              "Hint: you will probably need a Map.")
    random.seed()
    names = ['Alice', 'Bob', 'Charlie', 'Dave', 'Erin', 'Faythe', 'Grace', \
             'Heidi', 'Ingrid', 'Jay', 'Kostas', 'Lennart', 'Mallory', \
             'Nick', 'Oscar', 'Pat', 'Quentin', 'Rasmus', 'Sybil', 'Ted', \
             'Uma', 'Victor', 'Walter', 'Xerxes', 'Yoko', 'Zoe']
    relations = ["%s knows %s", "%s and %s both know each other"]
    name_map = dict()
    nrels = len(names)*(len(names)-1)/3
    for i in range(0, nrels):
        name1 = random.choice(names)
        names2 = copy.copy(names)
        names2.remove(name1)
        name2 = random.choice(names2)
        reln = random.randint(0, 1)
        if name1 not in name_map:
            name_map[name1] = [name1]
        if name2 not in name_map:
            name_map[name2] = [name2]
        if name1 not in name_map[name2]:
            name_map[name2] += [name1]
        if reln == 1 and name2 not in name_map[name1]:
                name_map[name1] += [name2]
        say(sock, (relations[reln] % (name1, name2)))
    appeared_names = name_map.keys()
    res = []
    while res == []:
        name = random.choice(appeared_names)
        reln = random.randint(0, 1)
        questions = ["Who knows %s?", "Who doesn't know %s?"]
        say(sock, (questions[reln] % name))
        res = name_map[name]
        if reln == 1:
            res = [ x for x in appeared_names if x not in res ]
        else:
            res.remove(name)
    res.sort()
    resl = map(lambda x : x.lower(), res)
    answer = ""
    mentioned = []
    garbage = None
    ok = True
    while ok and len(resl)>0:
        ready = select.select([sock], [], [], 5)
        if ready[0]:
            addanswer = sock.recv(1024).lower()
            if len(addanswer) == 0:
                break
            print "received %s" % addanswer
            sys.stdout.flush()
            answer += addanswer
            scanok = True
            while scanok and len(resl)>0 and ok:
                (scanok, nextname, answer) = scan(answer, \
                                                  string.ascii_lowercase)
                if scanok:
                    print "found name: %s" % nextname
                    if nextname.title() in appeared_names:
                        mentioned += [nextname.title()]
                    else:
                        garbage = nextname.title()
                    if nextname in resl:
                        resl.remove(nextname)
                        print "left: %s" % resl
                        sys.stdout.flush()
                    else:
                        ok = False
        else:
            ok = False
    if resl == []:
        say(sock, "wow! soooo coool! (=^-^=) next level port 9002")
        return True
    else:
        if mentioned == []:
            msg = "you didn't say anything meaningful."
        else:
            msg = "that wasn't quite right. " \
                  "you mentioned %s, but" % (", ".join(mentioned))
            if garbage is None:
                wrongperson = [ x for x in mentioned if x not in res ]
                if wrongperson != []:
                    wrongperson = wrongperson[0]
                    msg = "%s %s is not the right person." % (msg, wrongperson)
                else:
                    seen = []
                    dup = None
                    for x in mentioned:
                        if x not in seen:
                            seen += [x]
                        else:
                            dup = x
                            break
                    if dup is not None:
                        msg = "%s you should only mention %s once." % (msg, dup)
                    else:
                        msg = "%s something went wrong." % msg
        if garbage:
            msg = "%s I don't know who is %s." % (msg, garbage)
        say(sock, "%s the correct answer is, " \
                  "in any order: %s" % (msg, ", ".join(res)))
        return False

def level3(sock, remote):
    say(sock, "now it's your turn to ask. " \
              "I will try to connect to your port 8000 now. " \
              "if you are not listening, connect to my port 9002 " \
              "again when you're ready. " \
              "hint: start listening before connecting to my port 9002")
    try:
        sock2 = socket.create_connection((remote[0], 8000))
    except Exception:
        say(sock, "you don't listen :(")
        return False
    say(sock2, "cool. now ask me some 2+2 kinda question.")
    while True:
        ready = select.select([sock, sock2], [], [], 5)
        if ready[0]:
            if ready[0][0] == sock:
                say(sock, "now I don't speak to you on this socket. " \
                          "use the other one.")
            elif ready[0][0] == sock2:
                ask = sock2.recv(1024)
                (res, a, ask) = scan(ask, string.digits)
                if not res:
                    say(sock2, "I did not understand that. bye.")
                    return False
                (res, sign, ask) = scan(ask, ['+', '-', '*', '/'])
                if not res:
                    say(sock2, "I did not understand that. bye.")
                    return False
                (res, b, ask) = scan(ask, string.digits)
                if not res:
                    say(sock2, "I did not understand that. bye.")
                    return False
                a = long(a)
                b = long(b)
                sys.stdout.write("%d %s %d = " % (a, sign, b))
                if a == 2 and b == 2 and sign == '+':
                    toprint = "5 hehe"
                elif sign == '+':
                    toprint = "%d" % (a+b)
                elif sign == '-':
                    toprint = "%d" % (a-b)
                elif sign == '*':
                    toprint = "%d" % (a*b)
                elif sign == '/':
                    toprint = "%d" % (a/b)
                say(sock2, toprint)
                say(sock2, "nice! ^^ next level port 9003")
                return True
        else:
            say(sock2, "soooo sloooow! try again")
            return False

def level4(sock, remote):
    say(sock, "Different people listen on different sockets. " \
              "I will tell you the ports they are listening on. " \
              "First, say hello to all of them. They will reply. " \
              "Then I will ask you questions and tell you a name. " \
              "You will need to send an answer to the correct person.")
    random.seed()
    names = ['Alice', 'Bob', 'Charlie', 'Dave', 'Erin', 'Faythe', 'Grace', \
             'Heidi', 'Ingrid', 'Jay', 'Kostas', 'Lennart', 'Mallory', \
             'Nick', 'Oscar', 'Pat', 'Quentin', 'Rasmus', 'Sybil', 'Ted', \
             'Uma', 'Victor', 'Walter', 'Xerxes', 'Yoko', 'Zoe']
    lsockmap = dict()
    sockmap = dict()
    portrange = range(9100, 9200)
    try:
        for _ in range(0, 2*len(names)/3):
            name = random.choice(names)
            names.remove(name)
            port = random.choice(portrange)
            portrange.remove(port)
            lsock = socket.socket()
            lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            lsock.bind(("0.0.0.0",port))
            lsock.listen(1)
            say(sock, "%s is listening on port %d" % (name, port))
            lsockmap[lsock] = name
        say(sock, "Now say hello to everyone")
        while len(sockmap) < len(lsockmap):
            ready = select.select([sock]+lsockmap.keys(), [], [], 5)
            if ready[0]:
                if ready[0][0] == sock:
                    sock.recv(1024)
                    say(sock, "Not here")
                else:
                    lsock = ready[0][0]
                    (sock2, _) = lsock.accept()
                    sockmap[lsockmap[lsock]] = sock2
                    buf = sock2.recv(1024)
                    if buf.lower().find("hello") > -1:
                        say(sock2, "hello hello!")
            else:
                say(sock, "Your time is out. Try again.")
                return False
        names = sockmap.keys()
        for _ in range(0,1000):
            (question, correct) = arithmetic()
            name = random.choice(names)
            say(sock, "Tell %s what is %s" % (name, question))
            ready = select.select([sock]+sockmap.values(), [], [], 5)
            if ready[0]:
                if ready[0][0] == sockmap[name]:
                    sock2 = sockmap[name]
                    result = sock2.recv(1024)
                    intresult = int(result.strip())
                    print "%s: %s = %d" % (name, question, intresult)
                    sys.stdout.flush()
                    if intresult == correct:
                        say(sock2, "ok")
                    else:
                        say(sock, "wrong. too bad :(")
                        return False
                elif ready[0][0] == sock:
                    say(sock, "you must respond to %s! start over" % name)
                    return False
                else:
                    say(sock, "this is the wrong person!")
                    return False
            else:
                say(sock, "you have to respond quicker, try again")
                return False
        say(sock, "smart! next level port 9004")
        return True
    finally:
        map(lambda x : x.close(), sockmap.values()+lsockmap.keys())

def nyi(sock, remote):
    say(sock, "there isn't anything yet. come back later.")
    return False

############ utility functions

def say(sock, phrase):
    print phrase
    sys.stdout.flush()
    sock.send(phrase + "\n")

def scan(line, chars):
    started = False
    acc = ""
    while len(line)>0:
        if line[0] in chars:
            started = True
            acc += line[0]
        elif started:
            break
        line = line[1:]
    if acc != "":
        return (True, acc, line)
    else:
        return (False, "", line)

############ main routine

if __name__ == "__main__":
    try:
        main({ 9000 : level1,
               9001 : level2,
               9002 : level3,
               9003 : level4,
               9004 : nyi })
    except KeyboardInterrupt:
        print "bye bye!"
    sys.stdout.flush()
