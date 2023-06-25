FROM bd0276add33561b5011d22e581949fa90273e57e092f60461e3377b8b592a69e
LABEL authors="Tom Metz, Malte Königstein"

WORKDIR /linefollower

COPY . /linefollower

VOLUME /tmp/argus_socket /tmp/argus_socket

EXPOSE 8888/udp 80


#ENTRYPOINT ["top", "-b"]