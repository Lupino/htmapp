from uhashring import HashRing


def get_prefix_subfix(func):
    prefix, subfix = tuple(func.split('hotgym'))
    return prefix + '{}' + subfix


async def get_nodes(client):
    st = await client.status()
    funcs = [get_prefix_subfix(k) for k in st.keys() if k.find('hotgym') > -1]
    hr = HashRing(funcs, hash_fn='ketama')
    return hr


async def get_func_name(client, func, metric):
    hr = await get_nodes(client)
    tpl = hr.get_node(metric)
    return tpl.format(func)
