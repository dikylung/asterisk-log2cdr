__author__ = 'michel'

import csv
from datetime import datetime
import sys

class Call(object):
    def __init__(self, id, caller, start_time, receiver=None, end_time=None):
        self.id = id
        self.caller = caller
        self.start_time = start_time
        self.receiver = receiver
        self.end_time = end_time

    def duration(self):
        return self.end_time - self.start_time

class LogEntry(object):
    TSTAMP_FMT = '%Y %b %d %H:%M:%S'
    def __init__(self, year, line):
        self.tstamp = datetime.strptime('{0} {1}'.format(year, line[1:16]), self.TSTAMP_FMT)
        splits = line[18:].split()
        # parse log severity and ID
        index_of_bracket = splits[0].find('[')
        self.severity = splits[0][:index_of_bracket]
        self.event_id = int(splits[0][index_of_bracket+1:-1])
        # discard the trailing ':' from log source
        self.src = splits[1][:-1]
        # retrieve the log message
        self.msg = line[line.find(splits[1]) + len(splits[1]) + 1:]


class Log2CDR(object):

    def __init__(self, logfname, csvfname):
        self.logfname = logfname
        self.csvfname = csvfname
        self.calls = {}
        self.ok_count = 0
        self.err_count = 0

    def process_calls(self, start_time, end_time):
        if start_time.year != end_time.year:
            raise NotImplementedError('Support for processing time range spanning end-of-year not implemented')

        with open(self.logfname, 'rt') as logfile:
            with open(self.csvfname, 'a') as csvfile:
                csvwriter = csv.writer(csvfile)
                for line in logfile:
                    try:
                        log_entry = LogEntry(start_time.year, line)
                    except ValueError:
                        print("Cannot parse line: " + line)
                        continue
                    if log_entry.tstamp < start_time:
                        continue
                    if log_entry.tstamp > end_time:
                        break
                    if log_entry.src == 'pbx.c':
                        i = log_entry.msg.find('Set(CDR(accountcode)=')
                        if i != -1:
                            #print('Found call start: id={0} time={1}'.format(log_entry.event_id, log_entry.tstamp))
                            if log_entry.event_id in self.calls:
                                sys.stderr.write('Currently cannot handle reused event IDs: {0}'.format(log_entry.event_id))
                                sys.stderr.flush()
                                self.err_count += 1
                            else:
                                ph_start_i = i + len('Set(CDR(accountcode)=')
                                ph_end_i = log_entry.msg.find(')', ph_start_i)
                                ph_caller = log_entry.msg[ph_start_i:ph_end_i]
                                self.calls[log_entry.event_id] = Call(
                                    log_entry.event_id,
                                    ph_caller,
                                    log_entry.tstamp)
                        elif log_entry.msg.find('-- Goto (macro-hangupcall') != -1:
                            #print('Found call end: id={0} time={1}'.format(log_entry.event_id, log_entry.tstamp))
                            try:
                                call = self.calls[log_entry.event_id]
                                call.end_time = log_entry.tstamp
                                csvwriter.writerow([call.start_time,
                                                    call.caller, # should be caller id
                                                    call.caller, # src
                                                    call.receiver, # dst
                                                    call.duration()
                                ])
                                self.ok_count += 1
                                del self.calls[log_entry.event_id]
                            except KeyError:
                                sys.stderr.write('Processing end before call start:\n{0}\n'.format(line))
                                sys.stderr.flush()
                                self.err_count += 1

                    elif log_entry.src == 'app_dial.c' and log_entry.msg.find('-- Called SIP/') != -1:
                        #print('Found receiver: id={0}'.format(log_entry.event_id) + log_entry.msg)
                        ph_rcvr = log_entry.msg.split('/')[-1][:-1]
                        try:
                            call = self.calls[log_entry.event_id]
                            call.receiver = ph_rcvr
                        except KeyError:
                            sys.stderr.write('Processing receiver before call start:\n{0}\n'.format(line))
                            sys.stderr.flush()
                            self.err_count += 1
#                    if log_entry.msg.find('record-enable,,') != -1:
#                        pass
                print('Processed: {0} calls'.format(self.ok_count))
                print('Pending:   {0} calls'.format(len(self.calls)))
                print('Errors:    {0} lines'.format(self.err_count))
