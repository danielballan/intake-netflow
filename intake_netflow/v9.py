from datetime import datetime
import struct

import attr
import enum

from .utils import byte_stream, read_and_unpack


s_header = struct.Struct("!HHIIII")
s_flowset = struct.Struct("!H")
s_type_length = struct.Struct("!HH")


class FieldType(enum.Enum):
    IN_BYTES = (1, int)
    IN_PKTS = (2, int)
    FLOWS = (3, int)
    PROTOCOL = (4, int)
    SRC_TOS = (5, int)
    TCP_FLAGS = (6, int)
    L4_SRC_PORT = (7, int)
    IPV4_SRC_ADDR = (8, int)
    SRC_MASK = (9, int)
    INPUT_SNMP = (10, int)
    L4_DST_PORT = (11, int)
    IPV4_DST_ADDR = (12, int)
    DST_MASK = (13, int)
    OUTPUT_SNMP = (14, int)
    IPV4_NEXT_HOP = (15, int)
    SRC_AS = (16, int)
    DST_AS = (17, int)
    BGP_IPV4_NEXT_HOP = (18, int)
    MUL_DST_PKTS = (19, int)
    MUL_DST_BYTES = (20, int)
    LAST_SWITCHED = (21, int)
    FIRST_SWITCHED = (22, int)
    OUT_BYTES = (23, int)
    OUT_PKTS = (24, int)
    MIN_PKT_LNGTH = (25, int)
    MAX_PKT_LNGTH = (26, int)
    IPV6_SRC_ADDR = (27, bytes)
    IPV6_DST_ADDR = (28, bytes)
    IPV6_SRC_MASK = (29, int)
    IPV6_DST_MASK = (30, int)
    IPV6_FLOW_LABEL = (31, bytes)
    ICMP_TYPE = (32, int)
    MUL_IGMP_TYPE = (33, int)
    SAMPLING_INTERVAL = (34, int)
    SAMPLING_ALGORITHM = (35, int)
    FLOW_ACTIVE_TIMEOUT = (36, int)
    FLOW_INACTIVE_TIMEOUT = (37, int)
    ENGINE_TYPE = (38, int)
    ENGINE_ID = (39, int)
    TOTAL_BYTES_EXP = (40, int)
    TOTAL_PKTS_EXP = (41, int)
    TOTAL_FLOWS_EXP = (42, int)
    IPV4_SRC_PREFIX = (44, int)
    IPV4_DST_PREFIX = (45, int)
    MPLS_TOP_LABEL_TYPE = (46, int)
    MPLS_TOP_LABEL_IP_ADDR = (47, int)
    FLOW_SAMPLER_ID = (48, int)
    FLOW_SAMPLER_MODE = (49, int)
    FLOW_SAMPLER_RANDOM_INTERVAL = (50, int)
    MIN_TTL = (52, int)
    MAX_TTL = (53, int)
    IPV4_IDENT = (54, int)
    DST_TOS = (55, int)
    IN_SRC_MAC = (56, bytes)
    OUT_DST_MAC = (57, bytes)
    SRC_VLAN = (58, int)
    DST_VLAN = (59, int)
    IP_PROTOCOL_VERSION = (60, int)
    DIRECTION = (61, int)
    IPV6_NEXT_HOP = (62, bytes)
    BPG_IPV6_NEXT_HOP = (63, bytes)
    IPV6_OPTION_HEADERS = (64, int)
    MPLS_LABEL_1 = (70, bytes)
    MPLS_LABEL_2 = (71, bytes)
    MPLS_LABEL_3 = (72, bytes)
    MPLS_LABEL_4 = (73, bytes)
    MPLS_LABEL_5 = (74, bytes)
    MPLS_LABEL_6 = (75, bytes)
    MPLS_LABEL_7 = (76, bytes)
    MPLS_LABEL_8 = (77, bytes)
    MPLS_LABEL_9 = (78, bytes)
    MPLS_LABEL_10 = (79, bytes)
    IN_DST_MAC = (80, bytes)
    OUT_SRC_MAC = (81, bytes)
    IF_NAME = (82, str)
    IF_DESC = (83, str)
    SAMPLER_NAME = (84, str)
    IN_PERMANENT_BYTES = (85, int)
    IN_PERMANENT_PKTS = (86, int)
    FRAGMENT_OFFSET = (88, int)
    FORWARDING_STATUS = (89, int)
    MPLS_PAL_RD = (90, bytes)
    MPLS_PREFIX_LEN = (91, int)
    SRC_TRAFFIC_INDEX = (92, int)
    DST_TRAFFIC_INDEX = (93, int)
    APPLICATION_DESCRIPTION = (94, str)
    APPLICATION_TAG = (95, bytes)
    APPLICATION_NAME = (96, str)
    POST_IP_DIFF_SERV_CODE_POINT = (98, int)
    REPLICATION_FACTOR = (99, int)
    LAYER2_PACKET_SECTION_OFFSET = (102, int)
    LAYER2_PACKET_SECTION_SIZE = (103, int)
    LAYER2_PACKET_SECTION_DATA = (104, bytes)

    def __init__(self, id, dtype):
        self.id = id
        self.dtype = dtype


@attr.s
class Header(object):
    version = attr.ib(type=int, default=9)
    count = attr.ib(type=int, default=0)
    uptime = attr.ib(type=int, default=0)
    datetime = attr.ib(type=int)
    sequence = attr.ib(type=int, default=0)
    source_id = attr.ib(type=int, default=0)

    @datetime.default
    def current_unix_seconds(self):
        return int(datetime.utcnow().strftime("%s"))

    @staticmethod
    def decode(source):
        return Header(*read_and_unpack(source, s_header))

    def encode(self):
        return s_header.pack(self.version,
                             self.count,
                             self.uptime,
                             self.datetime,
                             self.sequence,
                             self.source_id)


def decode_flowset(source):
    raw = source.peek(s_flowset.size)[:s_flowset.size]
    flowset_id = s_flowset.unpack(raw)[0]
    if flowset_id == 0:
        return TemplateFlowSet.decode(source)
    if flowset_id > 255:
        return DataFlowSet.decode(source)
    raise Exception("unknown flowset id '{}'".format(flowset_id))


def create_struct(dtype, length):
    if dtype is int:
        if length == 1:
            code = 'B'
        elif length == 2:
            code = 'H'
        elif length == 4:
            code = 'I'
        elif length == 8:
            code = 'Q'
        else:
            raise TypeError("invalid integer length: {}".format(length))
    elif dtype is bytes:
        code = "B" * length
    elif dtype is str:
        code = "{}s".format(length)
    else:
        raise TypeError("invalid datatype: {}".format(dtype))
    return struct.Struct('!' + code)


@attr.s
class TemplateField(object):
    type = attr.ib(type=FieldType)
    length = attr.ib(type=int)

    @property
    def struct(self):
        if not hasattr(self, 'struct'):
            self.struct = create_struct(self.type.dtype, self.length)
        return self.struct

    @staticmethod
    def decode(source):
        return TemplateField(*read_and_unpack(source, s_type_length))

    def encode(self):
        return s_type_length.pack(self.type, self.length)


class TemplateRecord(object):
    def __init__(self, id, fields=None):
        self.id = id
        self.fields = fields if fields else []

    def __eq__(self, other):
        return self.id == other.id and sorted(self.fields) == sorted(other.fields)

    def __len__(self):
        return s_type_length.size + len(self.fields) * s_type_length.size

    def __iter__(self):
        return iter(self.fields)

    @staticmethod
    def decode(source):
        template_id, nfields = read_and_unpack(source, s_type_length)

        template = TemplateRecord(template_id)
        for _ in range(nfields):
            template.fields.append(TemplateField.decode(source))

        return template

    def encode(self):
        raw = s_type_length.pack(self.id, len(self.fields))
        for field in self.fields:
            raw += field.encode()
        return raw


class TemplateFlowSet(object):
    def __init__(self, templates=None):
        self.id = 0
        self.templates = {template.id: template for template in templates} if templates else {}

    def __eq__(self, other):
        return self.id == other.id and self.templates == other.templates

    def __len__(self):
        nbytes = s_type_length.size
        for template in self.templates.values():
            nbytes += len(template)
        return nbytes

    def __getitem__(self, key):
        return self.templates[key]

    def __iter__(self):
        return iter(self.templates)

    @staticmethod
    def decode(source):
        fs = TemplateFlowSet()
        _, length = read_and_unpack(source, s_type_length)
        offset = s_type_length.size

        while offset < length:
            template = TemplateRecord.decode(source)
            fs.templates[template.id] = template
            offset += len(template)

        return fs

    def encode(self):
        raw = s_type_length.pack(self.id, len(self))
        for template in self.templates.values():
            raw += template.encode()
        return raw


class DataFlowSet(object):
    def __init__(self, id, payload=b''):
        self.id = id
        self.payload = payload

    def __len__(self):
        return s_type_length.size + len(self.payload)

    def __iter__(self):
        return iter(self.records)

    def apply(self, template):
        self.records = []
        source = byte_stream(self.payload)

        remaining = len(self.payload)
        while remaining > len(template):
            self.records.append([read_and_unpack(source, field.struct) for field in template])
            remaining -= len(template)

    @staticmethod
    def decode(source):
        id, length = read_and_unpack(source, s_type_length)
        payload = source.read(length - s_type_length.size)
        return DataFlowSet(id, payload)

    def encode(self):
        raw = s_type_length.pack(self.id, len(self))
        if self.payload:
            raw += self.payload
        return raw


class ExportPacket(object):
    def __init__(self, flowsets, header=None):
        self.header = header if header else Header(count=len(flowsets))
        self.flowsets = flowsets

    def __iter__(self):
        return iter(self.flowsets)

    @staticmethod
    def decode(source):
        header = Header.decode(source)
        flowsets = [decode_flowset(source) for _ in range(header.count)]
        return ExportPacket(flowsets, header=header)

    def encode(self):
        raw = self.header.encode()
        for flowset in self.flowsets:
            raw += flowset.encode()
        return raw


class Stream(object):
    def __init__(self, source):
        self._source = source

    def next(self):
        if self._source.peek() == b'':
            raise StopIteration
        return ExportPacket.decode(self._source)

    def __next__(self):
        return self.next()

    def __iter__(self):
        return self

    def close(self):
        return self._source.close()
