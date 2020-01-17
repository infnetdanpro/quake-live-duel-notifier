import os
from time import sleep
import argparse
import ipaddress
import requests
from playsound import playsound
from ping3 import ping


TIMEOUT = 5
MP3FILE = os.path.join(os.getcwd(), 'loop_electricity_05.wav')


class IpAddress:
    def __init__(self, ip_port):
        self.ip_port = ip_port

    def _validate(self) -> bool:
        try:
            ip_port_splited = self.ip_port.split(':')
            ip, port = ip_port_splited[0], int(ip_port_splited[1])
            try:
                ipaddress.ip_address(ip)
                return True
            except Exception as e:
                raise ValueError(e)
        except Exception as e:
            raise ValueError(e)

    def get(self):
        if self._validate():
            return self.ip_port
        else:
            raise ValueError('Error')


class EndpointQLStats:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def _validate(self) -> bool:
        if 'http://api.qlstats.net/' not in self.endpoint:
            return False
        return True

    def get(self):
        if self._validate():
            return self.endpoint
        else:
            raise ValueError('Error')


class ServerWatcher:
    def __init__(self, ip_port, endpoint, amount_for_notify):
        self.ip_port = IpAddress(ip_port)
        self.endpoint = EndpointQLStats(endpoint)
        self.amount_for_notify = int(amount_for_notify)
        if self.amount_for_notify <= 0:
            raise ValueError('Specify amount of players for notify more than zero')

    def watch(self):
        ping_info = int(ping(self.ip_port.get().split(':')[0], unit='ms'))
        print(f'Server ping: {ping_info} ms')
        while True:
            self.check_players()
            sleep(TIMEOUT)

    def check_players(self):
        server_info = self.request_info_from_api()
        if len(server_info['players']):
            print([f'{player["name"]}:{player.get("rating")}' for player in server_info['players']])
        if len(server_info['players']) >= self.amount_for_notify:
            self.play_sound(MP3FILE)

    def request_info_from_api(self):
        r = requests.get(self.endpoint.get()).json()
        if r.get('ok') is True:
            return r
        else:
            raise Exception(f'{self.endpoint}: {r.status_code}')

    def play_sound(self, mp3file):
        playsound(mp3file)


def get_locate_server(steam_id: int) -> str or None:
    endpoint = f'https://qlstats.net/api/player/{steam_id}/locate'
    locate = requests.get(endpoint).json()
    if locate['server'] == None:
        raise Exception('You are not on server')
    else:
        server_addr = IpAddress(locate['server'])
        return server_addr.get() if server_addr.get() else None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("steamid")
    args = parser.parse_args()

    ip_port = get_locate_server(args.steamid)
    endpoint = f'http://api.qlstats.net/api/server/{ip_port}/players'
    server = ServerWatcher(ip_port, endpoint, 2)
    server.watch()
