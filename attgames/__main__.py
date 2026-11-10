import argparse
import json
import sys
from .pipeline import produce, review, publish, store


def main():
    parser = argparse.ArgumentParser(description='ATT DOS GAMES — Fase 1 offline')
    commands = parser.add_subparsers(dest='command', required=True)
    production = commands.add_parser('produzir')
    production.add_argument('--tema', required=True)
    production.add_argument('--duracao', type=int, default=35)
    production.add_argument('--retomar', action='store_true', help='Retenta apenas failed/qc_failed; até 3 tentativas')
    for name in ('revisar', 'publicar', 'status'):
        command = commands.add_parser(name)
        command.add_argument('--id', required=True)
        if name == 'publicar':
            command.add_argument('--plataformas', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'produzir':
            result = produce(args.tema, args.duracao, args.retomar)
        elif args.command == 'revisar':
            result = review(args.id)
        elif args.command == 'publicar':
            result = publish(args.id, args.plataformas)
        else:
            result = store().get(args.id)
            result['events'] = store().events(args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('state') in {'failed', 'qc_failed'} else 0
    except (KeyError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
