import socket
import os
import time
import thread

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

IP = 'localhost'
PORT = 80
BUFFER_LENGTH = 1024
ROOT_PATH = "/home/yanivk/PycharmProjects/Networking/venv/Server/webroot"
SOCKET_TIMEOUT = 10

IMAGE_TYPES = ["jpg", "jpeg", "png", "gif"]
TEXT_TYPES = ["html", "txt"]
JAVA_SCRIPT = ["js"]
CSS = ["css"]
XHR = ["xhr"]

ALL_TYPES = ["jpg", "jpeg", "png", "gif", "html", "txt", "js", "css", "xhr"]

DEFAULT_FILE = "/index.html"
NOT_FOUND_FILE = "/FOROFOR.html"

global functions


def get_file_data(filename):
    try:
        file_handler = open(filename, 'rb')

        # read file content
        response_content = file_handler.read()
        file_handler.close()
        return response_content

    except:
        print ("Warning, file not found. Serving response code 404\n")

    return None


def initialize_server():
    global server_socket

    # Freeing up port after closure
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Binding the server to the IP and PORT, listen for clients
    server_socket.bind((IP, PORT))
    server_socket.listen(1)

    print "Server Initialized!"


def send_response(client_socket):
    global functions

    functions = {"calculate-next": calculate_next, "calculate-area": calculate_area}

    request = client_socket.recv(BUFFER_LENGTH)
    file_path, file_type = get_request(client_socket, request)

    if not ("__DATA__:=" in str(file_path)):
        file_data = get_file_data(file_path)
    elif "__DATA__:=" in str(file_path):
        file_data = file_path.split("=")[1].split(".")
        result = str(file_data[0])

        if len(file_data)-2 >= 1:
            result += "." + file_data[1]

        file_data = result

        print file_data

    if file_data:
        code = 200
        length = len(file_data)

    elif file_path == "Post":
        code = 200
        file_data = "Image uploaded!"
        length = len(file_data)

    else:
        code = 404
        file_data = get_file_data(NOT_FOUND_FILE.split("/")[1])  # because it has a "/" in the beginning
        length = len(file_data)

    header = generate_header(code, file_type, length)
    client_socket.send(header + file_data)


def get_request(client_socket, request):
    client_request = request

    request_as_string = bytes.decode(client_request)

    info_array = request_as_string.split(' ')

    print info_array

    try:
        req_type = info_array[0]
    except IndexError:
        print "WEIRD INDEX OUT OF BOUNDS"
        return None, None

    if req_type == "GET":

        try:
            file_path = info_array[1]
        except IndexError:
            print "WEIRD INDEX OUT OF BOUNDS"
            return None, None

        print file_path
        path_backup = file_path
        path_backup2 = file_path
        if ((file_path.split("/")[1]).split("?")[0]) in functions:
            print "is function"
            func = functions.get(str((path_backup.split("/")[1]).split("?")[0]))
            file_path = "__DATA__:="

            variables = []

            for variable in (path_backup2.split("/")[1]).split("?")[1].split("&"):
                variables.append(variable.split("=")[1])

            file_path += str(func(variables))
            file_path += ".xhr"

        if file_path == "/":
            file_path = DEFAULT_FILE

        try:
            path_back = file_path
            path_back2 = file_path
            file_type = file_path.split(".")[1]

            if not (file_type in ALL_TYPES):
                raise IndexError

            try:
                if file_type in ALL_TYPES and file_path.split("?")[0] == "/image":
                    print "here"
                    file_path = "/uploads/" + path_back2.split("?")[1].split("=")[1]
            except Exception as e:
                print e

        except IndexError:
            print "FILE NAME INVALID"
            file_type = file_path.split(".")[len(path_back.split(".")) - 1]

            if not (file_type in ALL_TYPES):
                print "REALLY IS NOT VALID"
                file_path = NOT_FOUND_FILE
                file_type = file_path.split(".")[1]

        finally:
            print "file_type = " + file_type

            abs_file_path = ROOT_PATH + file_path
            print "file_path = ", abs_file_path
            print "\n----------------------------------------------------------------\n"
            return abs_file_path, file_type

    elif req_type == "POST":
        try:
            file_path = info_array[1]
            length = info_array[5].split("Accept:")[0]
            print length
        except IndexError:
            print "WEIRD INDEX OUT OF BOUNDS"
            return None, None

        path_back = file_path
        if file_path.split("?")[0] == "/upload":
            upload_photo(client_socket, path_back.split("?")[1].split("=")[1], length)

        return "Post", None


def upload_photo(client_socket, name, length):
    print "Uploading photo " + name
    file_to_upload = open(ROOT_PATH + "/uploads/" + name, 'wb')
    print "Receiving..."

    length = int(length)

    buffer_thing = client_socket.recv(length)
    file_to_upload.write(buffer_thing)

    file_to_upload.close()
    print "Done Receiving"


def generate_header(code, file_type, length):

    if code == 200:
        header_code = "200 OK"
    elif code == 404:
        header_code = "404 OK"
    else:
        print "header_code invalid. serving code 404"
        header_code = "404 OK"

    if file_type in IMAGE_TYPES:
        content_type = "image/xyz"
    elif file_type in TEXT_TYPES:
        content_type = "text/html"
    elif file_type in JAVA_SCRIPT:
        content_type = "text/javascript"
    elif file_type in CSS:
        content_type = "text/css"
    elif file_type in XHR:
        content_type = "text/plain"
    else:
        print "File type of request is invalid. Serving default type .txt"
        content_type = "text/html"

    response_header = 'HTTP/1.1 ' + header_code +\
                      '\nContent-Type: ' + content_type + \
                      '\nContent-Length: ' + str(length) + \
                      '\n\n'

    return response_header.encode()


def conversation(client_socket, client_address):
    while True:
        send_response(client_socket)


def calculate_next(variables):
    print_list(variables)
    return int(variables[0]) + 1


def calculate_area(variables):
    print_list(variables)
    return (float(variables[0]) * float(variables[1]))/2.0


def main():
    global server_socket

    initialize_server()

    while True:
        # accept client
        client_socket, client_address = server_socket.accept()
        # start conversation with new client in parallel thread
        thread.start_new_thread(conversation, (client_socket, client_address))


def print_list(ls):
    for thing in ls:
        print thing


if __name__ == "__main__":
    main()
