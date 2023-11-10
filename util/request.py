class Request:

    def __init__(self, request: bytes):
        # TODO: parse the bytes of the request and populate the following instance variables

        decoded = request
        lines = decoded.split(b"\r\n")

        header = lines[0].split(b' ')

        httpversion, reqtype, path = ("", "", "")
        if len(header) < 3:
            self.method = reqtype
            self.path = path
            self.http_version = httpversion
            print("error: header not formatted correctly")

            return
        else:
            reqtype = header[0]
            path = header[1]
            httpversion = b" ".join(header[2:])

        idx = 1
        httpheaders = {}
        httpheaders["Cookie"] = {}
        while lines[idx] != b"":
            colonloc = lines[idx].find(b":")
            if colonloc == -1:
                print("error: missing colon in HTTP request header: ", str(lines[idx]))
            else:
                key = lines[idx][:colonloc].decode(errors="ignore").strip().rstrip()
                value = lines[idx][colonloc:]
                value = value.decode(errors="ignore")
                if len(value) > 1:
                    value = lines[idx][colonloc + 1:].decode(errors="ignore").strip().rstrip()
                else:
                    value = ""
                if key == "Cookie":
                    values = value.split(";")
                    for kvpair in values:
                        splitthepair = kvpair.split("=")
                        httpheaders["Cookie"][splitthepair[0].strip().rstrip()] = splitthepair[1].strip().rstrip()
                else:
                    httpheaders[key] = value
            idx += 1
        # when this while loop breaks, body possibly follows
        thebody = b""
        if idx+1 < len(lines):
            thebody = b"\r\n".join(lines[idx+1:])

        contentlength = 0
        if "Content-Length" in httpheaders:
            try:
                contentlength = int(httpheaders["Content-Length"])
            except:
                print("malformed content-length")
                contentlength = 0
            finally:
                thebody = thebody[:contentlength]

        self.body = thebody.decode()
        self.method = reqtype.decode()
        self.path = path.decode()
        self.http_version = httpversion.decode()
        self.headers = httpheaders


def testThis(reqstring):
    tested = Request(reqstring)
    print(
        f"{tested.body} is the body, {tested.method} is the method, {tested.path} is the path, the http version is "
        f"{tested.http_version}, and the headers are {tested.headers}")


#testThis(b"GET /fuckyou.htmlsdfasdfjaksldfj HTTP/20.000\r\nhappiness:no\r\nbananas: apples:oranges\r\nurmom:\r\nsadness\r\n\r\n")
#testThis(b"GET /hahahahaha.html HTTP/1.1\r\nhappiness:no\r\n\r\nextremely simple body")
#testThis(b"GET /hahahahaha.html HTTP/1.1\r\nhappiness:no\r\n\r\nextremely simple body UH OH\r\nCARRIAGE RETURN!!!")
#is Request being wonky? do the testcases!