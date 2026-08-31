from pysnmp.hlapi.v3arch.asyncio import *

import asyncio

async def main():
    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpEngine(),
        CommunityData('public'),
        await UdpTransportTarget.create(('192.168.1.100', 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0'))
    )

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print(errorStatus)
    else:
        for oid, value in varBinds:
            print(f'{oid} = {value}')

asyncio.run(main())