"""Live API tests against an actual Attio instance.

Requires ATTIO_API_KEY env var or .env.local file in the project root.
"""

import json
import os
import sys
from pathlib import Path


def load_token() -> str:
    token = os.environ.get("ATTIO_API_KEY")
    if token:
        return token
    env_file = Path(__file__).parent.parent / ".env.local"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ATTIO_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("Set ATTIO_API_KEY env var or add it to .env.local")


def pp(label: str, obj):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    if hasattr(obj, "model_dump"):
        print(json.dumps(obj.model_dump(), indent=2, default=str)[:2000])
    else:
        print(obj)


def main():
    from attio import SDK

    token = load_token()
    with SDK(oauth2=token) as sdk:

        # 1. Identify workspace
        print("\n[1/6] Identifying workspace...")
        me = sdk.meta.get_v2_self()
        pp("Workspace / Token Info", me)

        # 2. List objects
        print("\n[2/6] Listing objects...")
        objects = sdk.objects.get_v2_objects()
        for obj in objects.data:
            print(f"  - {obj.singular_noun} (slug={obj.api_slug}, id={obj.id})")

        # 3. Query first 5 people
        print("\n[3/6] Querying people (limit=5)...")
        people = sdk.records.post_v2_objects_object_records_query(
            object="people", limit=5
        )
        for rec in people.data:
            name = "unknown"
            name_vals = rec.values.get("name", [])
            if name_vals and hasattr(name_vals[0], "full_name"):
                name = name_vals[0].full_name
            email = ""
            email_vals = rec.values.get("email_addresses", [])
            if email_vals and hasattr(email_vals[0], "email_address"):
                email = f", email={email_vals[0].email_address}"
            print(f"  - {name}{email}")

        # 4. Query first 5 companies
        print("\n[4/6] Querying companies (limit=5)...")
        companies = sdk.records.post_v2_objects_object_records_query(
            object="companies", limit=5
        )
        for rec in companies.data:
            name = "unknown"
            name_vals = rec.values.get("name", [])
            if name_vals and hasattr(name_vals[0], "value"):
                name = name_vals[0].value
            domain = ""
            domain_vals = rec.values.get("domains", [])
            if domain_vals and hasattr(domain_vals[0], "domain"):
                domain = f", domain={domain_vals[0].domain}"
            print(f"  - {name}{domain}")

        # 5. List workspace members
        print("\n[5/6] Listing workspace members...")
        members = sdk.workspace_members.get_v2_workspace_members()
        for m in members.data:
            name = f"{m.first_name} {m.last_name}"
            print(f"  - {name} (email={m.email_address}, role={m.access_level})")

        # 6. List lists
        print("\n[6/6] Listing lists...")
        lists = sdk.lists.get_v2_lists()
        for lst in lists.data:
            print(f"  - {lst.name} (slug={lst.api_slug}, id={lst.id})")

    print("\n✅ All queries completed successfully!")


if __name__ == "__main__":
    main()
