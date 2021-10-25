#!/usr/bin/env python

import sys, getopt, os, boto3, urllib.request
from pathlib import Path
from os import path
from configparser import ConfigParser


def help():
    print("""Usage:
  pydo [-s <service/application>] [-n] [-e <env>] [-t <2fa key>] [-T] [-Y] [-u <aws username>] [-a <account number>] [-p <aws profile>] [-r <region>] <command>

  Options:
  -h shows help
  -s <service/application>
  -S sets a default service for pydo and writes it to a config file
  -n do not query parameter store. Can be used to only authenticate the cli session with -Y -t or -T 
  -e <env> take credentials from environment Dev, Test or Prod (permission required)
  -t <2fa key> takes the 2FA key from your aws account
  -T lets you type in the 2FA key from your aws account during runtime
  -Y uses Yubikey for MFA auth
  -r overwrites/sets a specific region 
  -q Quiet mode (less output)
  -u sets a specific username combined with -a gives you a faster runtime (otherwise this data needs to be retrieved via aws)
  -a sets a specific account number combined with -u gives you a faster runtime (otherwise this data needs to be retrieved via aws)
  -p if multiple aws profiles are available you can choose the profile otherwise pydo will use the default profile
  -c container mode(enable this to make pydo work in ecs and codebuild)
  <command> is the command to execute with environment variables injected.
  Note that parameter substitution is performed. It may be required to double escape.

  Examples:
  pydo echo '$SECRET_CUSTOMERSERVICE_UI_URL'
  or
  Windows
  pydo echo %SECRET_CUSTOMERSERVICE_UI_URL%  
  
  displays the parameters for the JVM in the Dev environment. Note the quoting of the variable.
""")


# try-catch for wrong parameter usage
try:
    opts, args = getopt.getopt(sys.argv[1:], 'S:s:t:u:Tnp:ia:qr:ue:hYc')
except:
    help()
    sys.exit()


def check(argv):
    for opt, arg in opts:
        # later maybe implement something like a switch case
        if opt == '-e':
            os.environ['OVERRIDE_ENV'] = arg
            continue
        elif opt == '-t':
            os.environ['TOKEN'] = arg
            continue
        elif opt == '-T':
            os.environ['TOKEN'] = input("Please enter token: \n")
            continue
        elif opt == '-Y':
            os.environ['USE_YUBI'] = 'true'
            continue
        elif opt == '-n':
            # Caution! This is set to the string "true" not an actual boolean because we use Environment variables
            # instead of normal vars. (This is done to ensure compatibility to the original credo / systems that
            # worked with credo)
            os.environ['PYDO_NO_PARAMETER'] = 'true'
            os.environ['CREDO_NO_AWS'] = 'true' # Credo compatibility flag
            os.environ['ENVIRONMENT'] = 'Local'
            continue
        elif opt == '-q':
            os.environ['PYDO_QUIET'] = 'true'
            continue
        elif opt == '-i':
            os.environ['INTERACTIVE'] = 'true'
            continue
        elif opt == '-u':
            os.environ['AWS_USERNAME'] = arg
            continue
        elif opt == '-a':
            os.environ['AWS_ACCOUNT'] = arg
            continue
        elif opt == '-p':
            os.environ['PROFILENAME'] = arg
            continue
        elif opt == '-r':
            os.environ['AWS_REGION'] = arg
            continue
        elif opt == '-s':
            os.environ['SERVICE'] = arg
            continue
        elif opt == '-c':
            os.environ['CONTAINERMODE'] = 'true'
            continue
        elif opt == '-S':
            pydoConfigWrite('DEFAULTSERVICE', arg)
            continue
        elif opt == '-h':
            help()
            sys.exit()
            continue
        else:
            help()
            sys.exit()


def getCofigPath():
    pydoDir = str(Path.home()) + "/.credopy/"
    pydoConfigPath = pydoDir + "config"
    configExists = False

    if path.exists(pydoConfigPath):
        configExists = True

    return (pydoConfigPath, pydoDir, configExists)


def pydoLoadConfig(config):
    for eachSelection in config.sections():
        for (eachKey, eachVal) in config.items(eachSelection):
            os.environ[eachKey.upper()] = str(eachVal)


def pydoConfigRead(pydoConfigPath):
    parser = ConfigParser()
    parser.read(pydoConfigPath)

    return parser


def pydoConfigWrite(key, value):
    pydoConfigPath, pydoDir, configExists = getCofigPath()
    config = ConfigParser()

    if not path.exists(pydoDir):
        os.mkdir(pydoDir)

    if path.exists(pydoConfigPath):
        config = pydoConfigRead(pydoConfigPath)
        config['DefaultParameters'][key] = value
    else:
        config['DefaultParameters'] = {
            key: value
        }

    with open(pydoConfigPath, 'w') as f:
        config.write(f)


def getAWSEnv(instanceID, clientEC2):
    if instanceID == None:
        os.environ['ENVIRONMENT'] = 'Dev'
        return
    response = clientEC2.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [instanceID]
            }
        ]
    )
    for pair in response['Tags']:
        if pair['Key'] == 'environment':
            os.environ['ENVIRONMENT'] = pair['Value']


def getSessionData():
    # get current default region/profil name
    tmpSession = boto3.session.Session()
    if tmpSession.region_name is None:
        # Did not found a better way to get current region
        # If run on an ec2 instance definitely open for more elegant approaches
        sessionRegion = urllib.request.urlopen(
            'http://169.254.169.254/latest/meta-data/placement/availability-zone',
            timeout=2
        ).read().decode()[:-1]

        # When we are here we know, that we are on an ec2 instance so we also can fetch the right instance-id
        os.environ['INSTANCEID'] = urllib.request.urlopen(
            'http://169.254.169.254/latest/meta-data/instance-id',
            timeout=2
        ).read().decode()
        sessionProfileName = None
    else:
        sessionRegion = tmpSession.region_name
        sessionProfileName = tmpSession.profile_name

    # Check if custom sessiondata was provided
    if os.getenv('AWS_REGION') is not None:
        sessionRegion = os.getenv('AWS_REGION')

    if os.getenv('PROFILENAME') is not None:
        sessionProfileName = os.getenv('PROFILENAME')

    return (sessionRegion, sessionProfileName)


def printInfo():
    print("ENVIRONMENT: " + os.getenv('ENVIRONMENT'))

    if os.getenv('CONTAINERMODE') == 'true':
        print('Container mode enabled!')

    if os.getenv('CREDO_NO_AWS') == 'true':
        print('Skipped fetching parameters from AWS.')

    if os.getenv('AVAILABILITY_ZONE') is not None:
        print('ZONE: ' + os.getenv('AVAILABILITY_ZONE'))

    if os.getenv('INSTANCEID') is not None:
        print('INSTANCE: ' + os.getenv('INSTANCEID'))

    sessionRegion, sessionProfileName = getSessionData()
    print('REGION: ' + sessionRegion)
    if sessionProfileName is not None:
        print('PROFILNAME:' + sessionProfileName)

    if os.getenv('AWS_USERNAME') is not None:
        print('AWS_USERNAME: ' + os.getenv('AWS_USERNAME'))

    if os.getenv('AWS_ACCOUNT') is not None:
        print('AWS_ACCOUNT: ' + os.getenv('AWS_ACCOUNT'))

    print('')


def getAWSUsernameAndAccount(clientSTS):
    if None in (os.getenv('AWS_USERNAME'), os.getenv('AWS_ACCOUNT')):
        callerIdentity = clientSTS.get_caller_identity()

        if os.getenv('AWS_USERNAME') is None:
            os.environ['AWS_USERNAME'] = callerIdentity["Arn"].partition("/")[2]

        if os.getenv('AWS_ACCOUNT') is None:
            os.environ['AWS_ACCOUNT'] = callerIdentity['Account']

        return (os.getenv('AWS_USERNAME'), os.getenv('AWS_ACCOUNT'))
    else:
        return (os.getenv('AWS_USERNAME'), os.getenv('AWS_ACCOUNT'))


def getBotoClients():
    useSession = (os.getenv('AWS_REGION') is not None or os.getenv('PROFILENAME') is not None)

    sessionRegion, sessionProfileName = getSessionData()

    if (useSession):
        try:
            if os.getenv('CONTAINERMODE') == 'true':
                containerCredentials = urllib.request.urlopen(
                    'http://169.254.170.2' + os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"),
                    timeout=2
                ).read().decode()
                session = boto3.Session(
                    region_name=sessionRegion,
                    aws_access_key_id=containerCredentials["AccessKeyId"],
                    aws_secret_access_key=containerCredentials["SecretAccessKey"]
                )
            else:
                session = boto3.Session(profile_name=sessionProfileName, region_name=sessionRegion)
            os.environ['SESSION_REGION_NAME'] = session.region_name
            clientSTS = session.client('sts')
            clientEC2 = session.client('ec2')
        except Exception as e:
            print("Wrong profile name and/or region! Exception: " + e)
            sys.exit()
    else:
        clientSTS = boto3.client('sts', region_name=sessionRegion)
        clientEC2 = boto3.client('ec2', region_name=sessionRegion)

    return (clientSTS, clientEC2)

def isQuietModeEnabled():
    if os.getenv('PYDO_QUIET') is None:
        printInfo()
        return False
    return True

def app():
    if os.getenv('SERVICE') is None:
        os.environ['SERVICE'] = os.getenv('DEFAULTSERVICE')

    stsSessionData = None

    clientSTS, clientEC2 = getBotoClients()

    if (
            os.getenv('OVERRIDE_ENV') == 'Prod' and
            os.getenv('INTERACTIVE') == 'true'
    ):
        print('May not use interactive mode on Prod!')
        sys.exit()

    if os.getenv('USE_YUBI') == 'true':
        # With ykman as a workaround for missing hardware token integration from aws
        awsUsername, awsAccount = getAWSUsernameAndAccount(clientSTS)
        os.environ['TOKEN'] = os.popen('ykman oath accounts code ' + awsUsername).read().split(' ')[-1][:-1]

    if os.getenv('TOKEN') is not None:

        awsUsername, awsAccount = getAWSUsernameAndAccount(clientSTS)

        if os.getenv('INTERACTIVE') == 'true':
            sessionSeconds = 28800
        else:
            sessionSeconds = 900

        try:
            # When hardware MFAs are supported use this to be flexible whether use hard- or software-MFA:
            # serialNumber = boto3.client('iam').list_mfa_devices()['MFADevices'][0]['SerialNumber']

            # Until then use this, it is faster because it does not need to fetch the MFA device for the user
            serialNumber = "arn:aws:iam::" + awsAccount + ":mfa/" + awsUsername

            stsSessionData = clientSTS.get_session_token(
                DurationSeconds=sessionSeconds,
                SerialNumber=serialNumber,
                TokenCode=os.getenv('TOKEN')
            )
        except:
            print('Wrong MFA token or MFA device(pydo currently only supports virtual MFA devices)')
            print("Feel free to drop a comment about this: https://github.com/aws/aws-cli/issues/3607")
            sys.exit()

    if os.getenv('PYDO_NO_PARAMETER') == 'true':
        pass
    else:
        if os.getenv('AWS_REGION') is None and (
                os.getenv('AWS_REGION') is not None or os.getenv('PROFILENAME') is not None
        ):
            os.environ['AWS_REGION'] = os.getenv('SESSION_REGION_NAME')
        elif os.getenv('AWS_REGION') is not None:
            pass
        else:
            sessionRegion, sessionProfileName = getSessionData()
            os.environ['AWS_REGION'] = sessionRegion

        getAWSEnv(os.getenv('INSTANCEID'), clientEC2)

        if os.getenv('OVERRIDE_ENV') is not None:
            os.environ['ENVIRONMENT'] = os.getenv('OVERRIDE_ENV')

        sessionRegion, sessionProfileName = getSessionData()

        if os.getenv('TOKEN') is not None:
            clientSSMMFA = boto3.Session(
                profile_name=sessionProfileName,
                region_name=sessionRegion,
                aws_access_key_id=stsSessionData["Credentials"]['AccessKeyId'],
                aws_secret_access_key=stsSessionData["Credentials"]['SecretAccessKey'],
                aws_session_token=stsSessionData["Credentials"]['SessionToken']
            ).client(
                'ssm'
            )
        else:
            if sessionProfileName is None:
                clientSSMMFA = boto3.Session(
                    region_name=sessionRegion
                ).client(
                    'ssm'
                )
            else:
                clientSSMMFA = boto3.Session(
                    profile_name=sessionProfileName,
                    region_name=sessionRegion
                ).client(
                    'ssm'
                )

        ssmPath = "/" + os.getenv('ENVIRONMENT') + "/" + os.getenv('SERVICE') + "/"

        response = clientSSMMFA.get_parameters_by_path(
            Path=ssmPath,
            Recursive=True,
            WithDecryption=True
        )

        quietMode = isQuietModeEnabled()

        for r in response['Parameters']:
            if not quietMode:
                print("SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace("/",
                                                                                                                   "_").upper())
            os.environ["SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace("/",
                                                                                                                    "_").upper()] = \
                r['Value']

        while (True):
            if 'NextToken' not in response:
                break
            response = clientSSMMFA.get_parameters_by_path(
                Path=ssmPath,
                Recursive=True,
                WithDecryption=True,
                NextToken=response['NextToken']
            )
            for r in response['Parameters']:
                if not quietMode:
                    print("SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace(
                        "/", "_").upper())
                os.environ[
                    "SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace("/",
                                                                                                                 "_").upper()] = \
                    r['Value']

    if os.getenv('PYDO_QUIET') is None and os.getenv('CREDO_NO_AWS') == 'true':
        printInfo()

    isWindows = False
    if os.name == 'nt':
        isWindows = True

    if args:
        if not isWindows:
            os.system('eval ' + '"' + ' '.join(args) + '"')
        else:
            os.system('call ' + ' '.join(args))

    if os.getenv('INTERACTIVE') == 'true':
        print('Starting an interactive command-line...')
        print('Environment: ' + os.getenv('ENVIRONMENT'))
        if not isWindows:
            os.system('bash')
        else:
            os.system('cmd')


def main():
    check(sys.argv[1:])

    pydoConfigPath, pydoDir, configExists = getCofigPath()

    if configExists:
        pydoLoadConfig(pydoConfigRead(pydoConfigPath))

    if os.getenv('DEFAULTSERVICE') is None and os.getenv('SERVICE') is None:
        print("Please configure a default service with pydo -S <DEFAULTSERVICE> or provide a service with -s <SERVICE>")
        sys.exit()

    app()


if __name__ == "__main__":
    main()
