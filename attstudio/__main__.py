import argparse
import threading
import webbrowser
import uvicorn
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description='ATT DOS GAMES Studio local')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--worker',nargs=2,metavar=('ROOT','JOB_ID'),help=argparse.SUPPRESS)
    parser.add_argument('--self-test',action='store_true',help='Valida o pacote, FFmpeg e renderização local')
    args=parser.parse_args()
    if args.worker:
        from .worker import execute
        execute(Path(args.worker[0]),args.worker[1])
        return
    if args.self_test:
        from .packaging import self_test
        self_test()
        return
    if not args.no_browser:
        threading.Timer(1.5,lambda:webbrowser.open(f'http://127.0.0.1:{args.port}')).start()
    from .api import create_app
    uvicorn.run(create_app(),host='127.0.0.1',port=args.port,workers=1)

if __name__=='__main__':main()
