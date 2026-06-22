import os

import uvicorn

from mock_backend.app import create_app


def main() -> None:
    port = int(os.environ.get("MOCK_API_PORT", "8020"))
    uvicorn.run(create_app(), host="0.0.0.0", port=port, access_log=False)


if __name__ == "__main__":
    main()
