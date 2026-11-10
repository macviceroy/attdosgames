import argparse
import json
import sys
from pathlib import Path
from pydantic import ValidationError
from .models import PublicationError, Submission
from .service import PublicationService


def main():
    parser = argparse.ArgumentParser(description='ATT DOS GAMES publicação — dry-run offline, sem envio real')
    sub = parser.add_subparsers(dest='command', required=True)
    dry = sub.add_parser('dry-run')
    dry.add_argument('--manifest', type=Path, required=True)
    dry.add_argument('--output', type=Path)
    for name in ('status', 'reconciliar'):
        p = sub.add_parser(name)
        p.add_argument('--id', required=True)
    sub.add_parser('publicar', help='Sempre bloqueado nesta fase')
    args = parser.parse_args()
    try:
        service = PublicationService()
        if args.command == 'dry-run':
            if args.manifest.stat().st_size > 65536:
                raise PublicationError('manifest_too_large', 'Manifesto excede 64 KiB')
            submission = Submission.model_validate_json(args.manifest.read_text())
            result = service.dry_run(submission)
        elif args.command == 'status':
            result = service.status(args.id)
        elif args.command == 'reconciliar':
            result = service.reconcile(args.id)
        else:
            service.live()
        encoded = json.dumps(result, ensure_ascii=False, indent=2)
        if getattr(args, 'output', None):
            args.output.write_text(encoded)
        print(encoded)
        states = [r['state'] for r in result.get('results', [result]) if 'state' in r]
        return 1 if any(s in {'simulation_unknown', 'simulation_failed'} for s in states) else 0
    except ValidationError as error:
        print(json.dumps({'error': 'invalid_manifest', 'fields': [list(e['loc']) for e in error.errors()]}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (PublicationError, OSError, ValueError) as error:
        print(json.dumps({'error': getattr(error, 'code', 'invalid_input'), 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
