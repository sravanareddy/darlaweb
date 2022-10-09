from deepgram import Deepgram
import asyncio
import sys

async def main():
    taskdir = sys.argv[1]
    api_key = sys.argv[2]
    # This is a little janky, but since this function is called as a subprocess, there
    # is no way to communicate back to the parent process. So we can only communicate via
    # the return code, so the process will just fail if the key is not valid
    try:
        dg = Deepgram(api_key)
        test_connection = await dg.transcription.live()
        await test_connection.finish()
    except:
        raise Exception("Invalid Deepgram API Key.")

if __name__ == "__main__":
    asyncio.run(main())