from dataclasses import dataclass, field
from typing import Optional, List, Union
import json
from datetime import datetime

class TagList(list):
    def __init__(self, initial_list=None):
        if initial_list is not None:
            if not isinstance(initial_list, list):
                raise TypeError("Initial value must be a list")
            # Validate and normalize the initial list
            initial_list = [self._validate_item(item) for item in initial_list]
        else:
            initial_list = []
        # Call the parent list class's __init__ with the validated list
        super().__init__(initial_list)

    def _validate_item(self, item):
        if not isinstance(item, str):
            raise TypeError("Only strings are allowed")
        if not item.startswith("tag:"):
            item = "tag:" + item
        return item
    
    def __contains__(self, item):
        # Call the original __contains__ method to check for the item as is
        if super().__contains__(item):
            return True
        # Check if the item exists without "tag:" prefix
        if isinstance(item, str):
            if not item.startswith("tag:"):
                return super().__contains__(f'tag:{item}')
            return super().__contains__(item)
        return False
    
    def append(self, item):
        item = self._validate_item(item)
        super().append(item)

    def extend(self, iterable):
        validated_items = [self._validate_item(i) for i in iterable]
        super().extend(validated_items)

    def __setitem__(self, index, item):
        item = self._validate_item(item)
        super().__setitem__(index, item)

    def insert(self, index, item):
        item = self._validate_item(item)
        super().insert(index, item)

    def __iadd__(self, other):
        if not isinstance(other, list):
            raise TypeError("Only lists can be added with '+='")
        self.extend(other)  # Use the extend method to ensure validation
        return self

@dataclass(kw_only=True)
class NodeInfo():
    ID: str
    PublicKey: str
    HostName: str
    DNSName: str
    OS: str
    UserID: int
    TailscaleIPs: Optional[List[str]]
    AllowedIPs: Optional[List[str]]
    Tags: Optional[TagList] = None
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
    PeerAPIURL: Optional[List[str]]
    Capabilities: Optional[List[str]]
    CapMap: Optional[dict] = None
    InNetworkMap: bool
    InMagicSock: bool
    InEngine: bool

    def serialize(self) -> str:
        """Serializes the object to JSON."""
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @classmethod
    def deserialize(cls, data) -> 'Status':
        if isinstance(data, str):
            data = json.loads(data)
        data['Tags'] = TagList(data['Tags']) if 'Tags' in data else TagList()
        return cls(**data)

@dataclass
class Self(NodeInfo):
    pass

@dataclass
class Peer(NodeInfo):
    pass

@dataclass
class Status:
    Version: str
    TUN: bool
    BackendState: str
    HaveNodeKey: Optional[bool]
    AuthURL: str
    TailscaleIPs: Optional[List[str]]
    Self: Self
    Health: List[str]
    MagicDNSSuffix: str
    CurrentTailnet: Optional[str]
    CertDomains: Optional[List[str]]
    Peer: Optional[List[Peer]]
    User: Optional[str]
    ClientVersion: Optional[str]

    def serialize(self) -> str:
        """Serializes the object to JSON."""
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @classmethod
    def deserialize(cls, data) -> 'Status':
        if isinstance(data, str):
            data = json.loads(data)
        data['Self'] = Self.deserialize(data['Self'])
        data['Peer'] = [Peer.deserialize(value) for value in data['Peer'].values()]
        return cls(**data)