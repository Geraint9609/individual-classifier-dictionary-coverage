"""Select LCMC/UCLA from authorized original splits; preserve ids and split names."""
import argparse
from pathlib import Path
from main import read_csv, write_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'private_data/corpus.csv')
    args = parser.parse_args()
    rows = []
    for split in ('train', 'dev', 'test'):
        for row in read_csv(args.dataset / f'{split}.csv'):
            if row['id'].split('_', 1)[0] in {'LCMC', 'UCLA'}:
                rows.append({**row, 'split': split})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.output, rows, ['id', 'tagged', 'classifier', 'split'])
    print(f'Selected {len(rows)} rows: {args.output}')


if __name__ == '__main__':
    main()
