from dataclasses import dataclass, field
from typing import Optional, List, Union
import json
from datetime import datetime

@dataclass
class Self:
    ID: str
    PublicKey: str
    HostName: str
    DNSName: str
    OS: str
    UserID: int
    TailscaleIPs: Optional[List[str]]
    Addrs: List[str]
    CurAddr: str
    Relay: str
    RxBytes: int
    TxBytes: int
    Created: str
    LastWrite: str
    LastSeen: str
    LastHandshake: str
    Online: bool
    ExitNode: bool
    ExitNodeOption: bool
    Active: bool
    PeerAPIURL: Optional[str]
    InNetworkMap: bool
    InMagicSock: bool
    InEngine: bool

@dataclass
class Status:
    Version: str
    TUN: bool
    BackendState: str
    AuthURL: str
    TailscaleIPs: Optional[List[str]]
    Self: Self
    Health: List[str]
    MagicDNSSuffix: str
    CurrentTailnet: Optional[str]
    CertDomains: Optional[List[str]]
    Peer: Optional[str]
    User: Optional[str]
    ClientVersion: Optional[str]

    def serialize(self) -> str:
        """Serializes the object to JSON."""
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @staticmethod
    def deserialize(data: str) -> 'Status':
        """Deserializes JSON string to a Status object."""
        dict_data = json.loads(data)
        dict_data['Self'] = Self(**dict_data['Self'])
        return Status(**dict_data)