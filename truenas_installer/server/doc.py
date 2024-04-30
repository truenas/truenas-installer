# -*- coding=utf-8 -*-
import json
import textwrap

from truenas_installer.server.method import methods

__all__ = ["generate_api_doc"]


def generate_api_doc():
    print("# API Specification")
    print()
    print("This API uses JSON-RPC 2.0: https://www.jsonrpc.org/specification")
    print()

    print("# Server methods")
    print()
    for method in sorted(methods.values(), key=lambda method: method.name):
        print(f"## {method.name}")
        print()
        print(textwrap.dedent(method.fn.__doc__).strip())
        print()
        if method.schema is not None:
            print("### Parameter jsonschema")
            print()
            print(textwrap.indent(json.dumps(method.schema, indent=2), "    "))
            print()
        if method.result_schema is not None:
            print("### Result jsonschema")
            print()
            print(textwrap.indent(json.dumps(method.result_schema, indent=2), "    "))
            print()

    print("# Client methods")
    print()
    print("## installation_progress")
    print()
    print("Server calls this method on the client to report installation progress. This method will only be called ")
    print("after the client initiates system installation and before the server reports its result.")
    print()
    print("### Parameter jsonschema")
    print()
    print(textwrap.indent(json.dumps({
        "type": "object",
        "properties": {
            "progress": {"type": "number"},
            "message": {"type": "text"},
        },
    }, indent=2), "    "))
    print()
