"""
This local server setup is for testing purposes.

Use a real server for production deployment.
"""
import logging
import uvicorn

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run("vmail.app:app", host="0.0.0.0", port=8001, log_level="info")
