import argparse
import asyncio

from backend.config.db_config import AsyncSessionLocal
from backend.services.rag import vectorize_resource


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource-id", type=int, default=None)
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        if args.resource_id is None:
            raise SystemExit("Please provide --resource-id")
        count = await vectorize_resource(db, resource_id=args.resource_id)
        print(f"resource_id={args.resource_id} chunks={count}")


if __name__ == "__main__":
    asyncio.run(main())
