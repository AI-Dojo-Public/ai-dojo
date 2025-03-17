from cyst.api.configuration import *

target = NodeConfig(
    active_services=[],
    passive_services=[
        PassiveServiceConfig(
            name="bash",
            owner="root",
            version=ConfigParameter("my-custom-version"),
            access_level=ConfigParameter("my-custom-access-level"),
            local=True,
        ),
        PassiveServiceConfig(
            name="lighttpd",
            owner="www",
            version="1.4.62",
            access_level=AccessLevel.LIMITED,
            local=False,
        )
    ],
    shell="bash",
    traffic_processors=[],
    interfaces=[],
    name="target"
)

attacker_service = ActiveServiceConfig(
            type="netsecenv_agent",
            name="attacker",
            owner="attacker",
            access_level=AccessLevel.LIMITED,
            ref="attacker_service_ref"
        )

attacker_node_1 = NodeConfig(
    active_services=[ConfigParameter("attacker_location_1")],
    passive_services=[],
    interfaces=[],
    shell="",
    traffic_processors=[],
    name="attacker_node_1"
)

attacker_node_2 = NodeConfig(
    active_services=[ConfigParameter("attacker_location_2")],
    passive_services=[],
    interfaces=[],
    shell="",
    traffic_processors=[],
    name="attacker_node_2"
)

router = RouterConfig(
    interfaces=[
        InterfaceConfig(
            ip=IPAddress("192.168.0.1"),
            net=IPNetwork("192.168.0.1/24"),
            index=0
        ),
        InterfaceConfig(
            ip=IPAddress("192.168.0.1"),
            net=IPNetwork("192.168.0.1/24"),
            index=1
        ),
        InterfaceConfig(
            ip=IPAddress("192.168.0.1"),
            net=IPNetwork("192.168.0.1/24"),
            index=2
        )
    ],
    traffic_processors=[
        FirewallConfig(
            default_policy=FirewallPolicy.ALLOW,
            chains=[
                FirewallChainConfig(
                    type=FirewallChainType.FORWARD,
                    policy=FirewallPolicy.ALLOW,
                    rules=[]
                )
            ]
        )
    ],
    id="router"
)

exploit1 = ExploitConfig(
    services=[
        VulnerableServiceConfig(
            service="lighttpd",
            min_version="1.3.11",
            max_version="1.4.62"
        )
    ],
    locality=ExploitLocality.REMOTE,
    category=ExploitCategory.CODE_EXECUTION,
    id="http_exploit"
)

connection1 = ConnectionConfig(
    src_ref=target.ref,
    src_port=-1,
    dst_ref=router.ref,
    dst_port=0
)

connection2 = ConnectionConfig(
    src_ref=attacker_node_1.ref,
    src_port=-1,
    dst_ref=router.ref,
    dst_port=1
)

connection3 = ConnectionConfig(
    src_ref=attacker_node_2.ref,
    src_port=-1,
    dst_ref=router.ref,
    dst_port=2
)

parametrization = ConfigParametrization(
    parameters=[
        ConfigParameterSingle(
            name="Vulnerable service version",
            value_type=ConfigParameterValueType.VALUE,
            description="Sets the version of a vulnerable service. If you put version smaller than 1.3.11 and larger than 1.4.62, the exploit will not work.",
            default="1.4.62",
            parameter_id="my-custom-version"
        ),
        ConfigParameterSingle(
            name="Vulnerable access level",
            value_type=ConfigParameterValueType.VALUE,
            description="Sets the access level for the service",
            default=AccessLevel.LIMITED,
            parameter_id="my-custom-access-level"
        ),
        ConfigParameterGroup(
            parameter_id="attacker-position",
            name="Attacker position",
            group_type=ConfigParameterGroupType.ANY,
            value_type=ConfigParameterValueType.REF_COPY,
            description="The node, where the attacker starts at.",
            default=["attacker_location_1", "attacker_location_2"],
            options=[
                ConfigParameterGroupEntry(
                    parameter_id="attacker_location_1",
                    value="attacker_service_ref",
                    description="Node 1"
                ),
                ConfigParameterGroupEntry(
                    parameter_id="attacker_location_2",
                    value="attacker_service_ref",
                    description="Node 2"
                )
            ]
        ),
    ]
)

all_configs = [
    target, attacker_service,
    attacker_node_1, attacker_node_2, router,
    exploit1, connection1, connection2, connection3,
    parametrization
]