from fastmcp.client import Client
from fastmcp.client.auth.bearer import BearerAuth
import asyncio
TEST_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiaXNzIjoiaHR0cHM6Ly90ZXN0LnlvdXJjb21wYW55LmNvbSIsImlhdCI6MTc1OTYyOTk4NywiZXhwIjoxNzU5NjMzNTg3LCJhdWQiOiJ0ZXN0LW1jcC1zZXJ2ZXIiLCJzY29wZSI6InJlYWQgd3JpdGUgYWRtaW4ifQ.k_Zy8Lvpn6Ww_htCudmHH-4Oybn8WiReF5BQSClBsyw1bCBqS5gIVrtyoddroGq8Vt2k9MeBM1GbuhvmqOzjCkVKdaqk4oWfI9It9EcC5AxnVW53q8ClecLgHNvo-uIXRbPl00fgtuO0cqDOPd5KoIXqlmH3U6i1xrXVnbqslNzkAzLlo6ApUSpF9_suBkxX68F5UK5DF_P9cRNDUeXJih5c651l9XNvTwesOrNGbaqn1bnTZbbs79Didp-e1aX7582l-ss1JxSmu3TTeEF1cXqQgz8toAUQyNcY8hW7uXiRECZqWs9q-q90ET2gWcfocav_zcvIgeDx0csPUHyO6g"

client = Client("http://localhost:8015/mcp", auth=BearerAuth(TEST_TOKEN))

async def main():
    async with client:
        tools = await client.list_tools()
        print(tools)

if __name__ == "__main__":
    asyncio.run(main())
