=====
Usage
=====

`logtailor` is a tail program and filter for log files. You can apply it to a copy of a logfile to filter for specific information, or on a log file of a running application to filter the log output in real time. 

After installing `logtailor` it is available as an executable. To get an overview just call:::

    logtailor --help

This will provide a list of all command line arguments with a short description.


Parsing a log file for some pattern
-----------------------------------

We have a copy of a log file and want to check for certain patterns, e.g., ERROR and WARN logs:::

    logtailor --log file.log --trigger=ERROR --trigger=WARN --history

`--trigger` is used to specify patterns to look for. We need to add `--history` to tell `logtailor` that also already existing log entries shall be considered.


Parsing a log file of a running application
-------------------------------------------

When tailing a log file of a running application care must be taken to keep the file open at eof and to wait for more data. This is accomplished with the `--tail` flag. For this use case it may be useful to process only log items that are written after starting the tail. This can be achieved with the `--no-history` flag, which is the default:::

    logtailor --log file.log --trigger=ERROR --tail

No we will see only log items matching our trigger criteria and that are emitted after start of `logtailor`. This is handy when running tests.

If we would set `--history` all log items written before would also be considered.


Using a configuration file
--------------------------

When working with the same logs and filters for some time, it gets tedious to enter the same command line arguments over and over again. In this case it is more convenient to use a configuration file. Create a file named `.logtailor.ini` in the folder you run the program. In the configuration file you can configure a list of log files you want to use. Assign a name to each log file to reference it later on:::

    [logfiles]
    log1 = ./logs/application/server.log
    log2 = ./logs/webserver/site.log

In a second section the output file and triggers can be configured:::

    [global]
    output = filtered.log

    triggers =
        ERROR
        interesting message
        server started

With such a configuration you can use the short log names instead of the paths to specify a logfile. All triggers in the configuration will be used automatically. More triggers can be added on the command line:::

    logtailor --log log2 --trigger=WARNING


Maintain triggers in configuration file
---------------------------------------

Having a configuration file is useful for a couple of use cases. One is easy management of a bigger set of trigger criteria:::

    logtailor --log logfile.log --tail

All triggers defined in the configuration will be used. More triggers can be added on the command line:::

    logtailor --log logfile.log --trigger=WARN --fail


Use shortcuts to specify log files
----------------------------------

Using the log file identifiers instead of the paths and file names is also convenient:::

    logtailor --log log1 --tail


Tail and filter multiple log files simultaneously
-------------------------------------------------

But one use case does only work with a configuration file: tailing multiple log files simultaneously:::

    logtailor --parse-all --tail

Dependend on `--tail` the log files will be processed sequentially (`--no-tail`) or in parallel (`--tail`).


Append to an existing target file
---------------------------------

The `--append` flag allows to append the output of the current session to an existing target file. Without this flag the target file is overwritten for each run:::

    logtailor --log=file.log --append

