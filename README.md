spraycharles
======
## Overview ##
Low and slow password spraying tool, designed to spray on an interval over a long period of time.


## Install ##

#### Using pipenv
```bash
git clone https://github.com/Tw1sm/spraycharles.git && cd spraycharles
pipenv --python 3 shell
pip3 install -r requirements.txt
./spraycharles.py -h
```


#### Using Docker
Build the container using the included Dockerfile.

```bash
git clone https://github.com/Tw1sm/spraycharles.git && cd spraycharles
docker build . -t spraycharles
```

You will most likely want to save and use a list of usernames and passwords during spraying. The easiest way to do this is by mapping a directory on your host with the container. Use the following command in Bash to map your present working directory to the spraycharles install directory inside the running container.

```bash
docker run -it -v $(pwd):/spraycharles/ spraycharles -h
```

Following your first run of the command above, a sparycharles directory will be created on your system where you can add username and password lists as well as access spraying logs. 

#### From GitHub
```bash
$ git clone https://github.com/Tw1sm/spraycharles.git
$ cd spraycharles
$ pip3 install -r requirements.txt
$ ./spraycharles.py -h
```

<br/>

## Usage ##
```
Usage: spraycharles.py [OPTIONS]

  Low and slow password spraying tool...

Options:
  -p, --passwords TEXT       Filepath of the passwords list or a single
                             password to spray.  [required]
  -u, --usernames TEXT       Filepath of the usernames list.  [required]
  -H, --host TEXT            Host to password spray (ip or hostname). Can by
                             anything when using Office365 module - only used
                             for logfile name.
  -m, --module TEXT          Module corresponding to target host.  [required]
  --path TEXT                NTLM authentication endpoint. Ex: rpc or ews
  -o, --output TEXT          Name and path of output csv where attempts will
                             be logged.
  -a, --attempts INTEGER     Number of logins submissions per interval (for
                             each user).
  -i, --interval INTEGER     Minutes inbetween login intervals.
  -e, --equal INTEGER        Does 1 spray for each user where password =
                             username.
  -t, --timeout INTEGER      Web request timeout threshold. Default is 5
                             seconds.
  -P, --port INTEGER         Port to connect to on the specified host. Default
                             is 443.
  -f, --fireprox TEXT        The url of the fireprox interface, if you are
                             using fireprox.
  -d, --domain TEXT          HTTP: Prepend DOMAIN\ to usernames. SMB: Supply
                             domain for smb connection.
  --analyze TEXT             Run the results analyzer after each spray
                             interval. False positives are more likely
  -j, --jitter INTEGER       Jitter time between requests in seconds.
  -jm, --jitter-min INTEGER  Minimum time between requests in seconds.
  --config FILE              Read configuration from FILE.
  -h, --help                 Show this message and exit.
```

#### Config File 
It is possible to pre-populate command line arguments form a configuration file using the --config argument.

An example configuration file is listed below:

```
userlist = '/tmp/users.txt'
passlist = '/tmp/passwords.txt'
csvfile = 'mail.acme.com.csv'
module = 'owa'
host = 'mail.acme.com'
domain = 'ACME'
analyze = 'True'
attempts = '1'
interval = '30'
timeout = '25'
```

Note: Due to internal script logic the following variables must be defined differently than they would be via CLI:

* usernames = userlist
* passwords = passlist
* output = csvfile

<br/>

### Examples ###
Basic usage (Office365)
```
./spraycharles.py -u users.txt -p passwords.txt -m Office365
```
Basic usage (non-Office365) with a single password, supplied via command line
```
./spraycharles.py -u users.txt -H webmail.company.com -p Password123 -m owa
```
Attempt 5 logins per user every 20 minutes
```
./spraycharles.py -n users.txt -H webmail.company.com -p passwords.txt -i 20 -a 5 -m owa
```
Usage with fireprox (Office365)
```
./spraycharles.py -u users.txt -p passwords.txt -m office365 -f abcdefg.execute-api.us-east-1.amazonawms.com
```
Spray host over SMB with 2 attempts per user every hour
```
./spraycharles.py -u users.txt -p passwords.txt -m Smb -H 10.10.1.5 -a 2 -i 60
```

<br/>

## Utilities ##
Spraycharles is packaged with some additional utilities to assist with spraying efforts.
<br/>

#### Generating Custom Spray Lists 
make_list.py will generate a password list based off the specifications provided in list_elements.json
```
./utils/make_list.py
```

<br/>

#### Extracting Domain from NTLM over HTTP and SMB 
ntlm_challenger.py will extract the internal domain from both NTLM over HTTP and SMB services using a command similar to the one listed below.


```
./utils/ntlm_challenger.py https://mail.acme.com/ews
```

<br/>

### Analyzing the results CSV file ###
`analyze.py` can read your output CSV and determine response lengths that are statistically relevant. With enough data, it should be able to pull successful logins out of your CSV file. This is not the only way to determine successful logins, depending on your target site, and I would still recommend checking the data yourself to be sure nothing is missed. For SMB, it will simply find entries that contain "SUCCESS"
```
./analyze.py myresults.csv
```

<br/>

## Disclaimer ##
This tool is designed for use during penetration testing; usage of this tool for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state and federal laws. Developers assume no liability and are not responsible for any misuse of this program.
