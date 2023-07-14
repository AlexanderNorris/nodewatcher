from peewee import *

database = MySQLDatabase(
    "stats",
    **{
        "charset": "utf8",
        "sql_mode": "PIPES_AS_CONCAT",
        "use_unicode": True,
        "host": "stats_db",
        "user": "stats",
        "password": "password",
    }
)


class UnknownField(object):
    def __init__(self, *_, **__):
        pass


class BaseModel(Model):
    class Meta:
        database = database


class Metric(BaseModel):
    clock = DateTimeField()
    handshake_latency = IntegerField()
    id = BigAutoField()
    tcp_latency = IntegerField()
    tcp_state = IntegerField()

    class Meta:
        table_name = "metric"


class Pool(BaseModel):
    active_epoch_no = IntegerField()
    active_stake = CharField()
    block_count = IntegerField()
    fixed_cost = CharField()
    id = BigAutoField()
    live_delegators = IntegerField()
    live_pledge = CharField()
    live_saturation = CharField()
    live_stake = CharField()
    margin = IntegerField()
    meta_hash = CharField()
    meta_json_description = CharField()
    meta_json_homepage = CharField()
    meta_json_name = CharField()
    meta_json_ticker = CharField()
    meta_url = CharField()
    op_cert = CharField()
    op_cert_counter = IntegerField()
    pledge = CharField()
    pool_id_bech32 = CharField(unique=True)
    pool_id_hex = CharField(unique=True)
    pool_status = CharField()
    retiring_epoch = IntegerField(null=True)
    reward_addr = CharField()
    sigma = CharField()
    vrf_key_hash = CharField(unique=True)

    class Meta:
        table_name = "pool"


class Owner(BaseModel):
    id = BigAutoField()
    owner_address = CharField()
    pool = ForeignKeyField(column_name="pool_id", field="id", model=Pool)

    class Meta:
        table_name = "owner"


class Relay(BaseModel):
    dns = CharField()
    id = BigAutoField()
    ipv4 = CharField()
    ipv6 = CharField()
    pool = ForeignKeyField(column_name="pool_id", field="id", model=Pool)
    port = IntegerField()
    srv = CharField()
    watcher_determined_state = CharField()

    class Meta:
        table_name = "relay"
