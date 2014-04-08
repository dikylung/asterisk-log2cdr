#!/usr/bin/python3

__author__ = 'michel'

import argparse
from datetime import datetime
import log2cdr


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log_file')
    parser.add_argument('csv_file')
    parser.add_argument('--start', help='starting cut-off for log entries')
    parser.add_argument('--end', help='ending cut-off for log entries')
    args = parser.parse_args()
    print(args.log_file)
    print(args.csv_file)

    if args.start:
        try:
            strt = datetime.strptime(args.start, log2cdr.LogEntry.TSTAMP_FMT)
        except ValueError:
            raise
    if args.end:
        try:
            endt = datetime.strptime(args.end, log2cdr.LogEntry.TSTAMP_FMT)
        except ValueError:
            raise

    if not args.start:
        strt = datetime.now().replace(month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
    if not args.end:
        endt = datetime.now().replace(month=12,day=31,hour=23,minute=59,second=59,microsecond=999999)


    print(strt)
    print(endt)

    converter = log2cdr.Log2CDR(args.log_file, args.csv_file)
    converter.process_calls(strt, endt)


