from uhashring import HashRing


def get_prefix_subfix(func):
    prefix, subfix = tuple(func.split('run_model'))
    return prefix + '{}' + subfix


def is_func(k):
    return k.find('run_model') > -1


async def get_nodes(client):
    st = await client.status()
    funcs = [get_prefix_subfix(k) for k in st.keys() if is_func(k)]
    hr = HashRing(funcs, hash_fn='ketama')
    return hr


async def get_func_name(client, func, metric):
    hr = await get_nodes(client)
    tpl = hr.get_node(metric)
    return tpl.format(func)
