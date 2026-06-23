import ipaddress


def parse_network(network):

    return ipaddress.ip_network(
        network,
        strict=False,
    )


def network_to_db_filename(network):

    net = parse_network(network)

    return (
        f"{net.network_address}"
        f"_{net.prefixlen}.db"
    )


def network_host_count(net):

    if net.version != 4:
        raise ValueError(
            "Only IPv4 is supported"
        )

    if net.prefixlen == 32:
        return 1

    if net.prefixlen == 31:
        return 2

    return 2 ** (32 - net.prefixlen) - 2


def network_contains(outer, inner):

    outer_net = parse_network(outer)
    inner_net = parse_network(inner)

    return (
        inner_net.subnet_of(outer_net)
        or inner_net == outer_net
    )
