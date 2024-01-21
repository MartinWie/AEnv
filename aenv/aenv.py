#!/usr/bin/env python

import boto3
import getopt
import logging
import os
import sys
import urllib.request
from configparser import ConfigParser
from os import path
from pathlib import Path
from botocore.exceptions import ClientError, BotoCoreError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the logging level for Boto3 to WARNING to suppress INFO messages
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('nose').setLevel(logging.WARNING)


def help():
    logging.info("""Usage:
  aenv [-s <service/application>] [-n] [-e <env>] [-t <2fa key>] [-T] [-Y] [-u <aws username>] [-a <account number>] [-p <aws profile>] [-r <region>] [-v] <command>

  Options:
  -h shows help
  -s <service/application>
  -S sets a default service for aenv and writes it to a config file
  -n do not query parameter store. Can be used to only authenticate the cli session with -Y -t or -T 
  -e <env> take credentials from environment Dev, Test or Prod (permission required)
  -t <2fa key> takes the 2FA key from your aws account
  -T lets you type in the 2FA key from your aws account during runtime
  -Y uses Yubikey for MFA auth
  -r overwrites/sets a specific region 
  -v Verbose mode (additional output)
  -u sets a specific username combined with -a gives you a faster runtime (otherwise this data needs to be retrieved via aws)
  -a sets a specific account number combined with -u gives you a faster runtime (otherwise this data needs to be retrieved via aws)
  -p if multiple aws profiles are available you can choose the profile otherwise aenv will use the default profile
  -c container mode(enable this to make aenv work in ecs and codebuild)
  <command> is the command to execute with environment variables injected.
  Note that parameter substitution is performed. It may be required to double escape.

  Examples:
  anev echo '$SECRET_CUSTOMERSERVICE_UI_URL'
  or
  Windows
  aenv echo %SECRET_CUSTOMERSERVICE_UI_URL%  
  
  displays the parameters for the JVM in the Dev environment. Note the quoting of the variable.
""")


# try-catch for wrong parameter usage
try:
    opts, args = getopt.getopt(sys.argv[1:], 'S:s:t:u:Tnp:ia:vr:ue:hYc')
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
            os.environ['AENV_NO_PARAMETER'] = 'true'
            os.environ['CREDO_NO_AWS'] = 'true'  # Credo compatibility flag
            os.environ['ENVIRONMENT'] = 'Local'
            continue
        elif opt == '-v':
            os.environ['AENV_VERBOSE'] = 'true'
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
            aenvConfigWrite('DEFAULTSERVICE', arg)
            continue
        elif opt == '-h':
            help()
            sys.exit()
            continue
        else:
            help()
            sys.exit()


def isVerboseModeEnabled():
    if os.getenv('AENV_VERBOSE') is not None:
        return True
    return False


def getCofigPath():
    aenvDir = str(Path.home()) + "/.aenv/"
    aenvConfigPath = aenvDir + "config"
    configExists = False

    if path.exists(aenvConfigPath):
        configExists = True

    return (aenvConfigPath, aenvDir, configExists)


def aenvLoadConfig(config):
    for eachSelection in config.sections():
        for (eachKey, eachVal) in config.items(eachSelection):
            os.environ[eachKey.upper()] = str(eachVal)


def aenvConfigRead(aenvConfigPath):
    parser = ConfigParser()
    parser.read(aenvConfigPath)

    return parser


def aenvConfigWrite(key, value):
    aenvConfigPath, aenvDir, configExists = getCofigPath()
    config = ConfigParser()

    if not path.exists(aenvDir):
        os.mkdir(aenvDir)

    if path.exists(aenvConfigPath):
        config = aenvConfigRead(aenvConfigPath)
        config['DefaultParameters'][key] = value
    else:
        config['DefaultParameters'] = {
            key: value
        }

    with open(aenvConfigPath, 'w') as f:
        config.write(f)


def getSessionData():
    # Check if custom session data was provided via environment variables first
    sessionRegion = os.getenv('AWS_REGION')
    sessionProfileName = os.getenv('PROFILENAME')

    # Only attempt to retrieve data from metadata service if AWS_REGION is not set
    if sessionRegion is None:
        tmpSession = boto3.session.Session()
        if tmpSession.region_name is None:
            # Attempt to retrieve region from EC2 instance metadata service
            try:
                sessionRegion = urllib.request.urlopen(
                    'http://169.254.169.254/latest/meta-data/placement/availability-zone',
                    timeout=10  # Increased timeout
                ).read().decode()[:-1]

                # Fetch instance ID as well
                os.environ['INSTANCEID'] = urllib.request.urlopen(
                    'http://169.254.169.254/latest/meta-data/instance-id',
                    timeout=10
                ).read().decode()
            except Exception as e:
                logging.error(f"Unable to access metadata service: {e}")
                # Handle the error or set default values
        else:
            # Use region and profile name from boto3 session
            sessionRegion = tmpSession.region_name
            sessionProfileName = tmpSession.profile_name

    # Return the region and profile name
    return (sessionRegion, sessionProfileName)


def printInfo():
    logging.info("ENVIRONMENT: " + os.getenv('ENVIRONMENT'))

    if os.getenv('CONTAINERMODE') == 'true':
        logging.info('Container mode enabled!')

    if os.getenv('CREDO_NO_AWS') == 'true':
        logging.info('Skipped fetching parameters from AWS.')

    if os.getenv('AVAILABILITY_ZONE') is not None:
        logging.info('ZONE: ' + os.getenv('AVAILABILITY_ZONE'))

    if os.getenv('INSTANCEID') is not None:
        logging.info('INSTANCE: ' + os.getenv('INSTANCEID'))

    sessionRegion, sessionProfileName = getSessionData()
    logging.info('REGION: ' + sessionRegion)
    if sessionProfileName is not None:
        logging.info('PROFILNAME:' + sessionProfileName)

    if os.getenv('AWS_USERNAME') is not None:
        logging.info('AWS_USERNAME: ' + os.getenv('AWS_USERNAME'))

    if os.getenv('AWS_ACCOUNT') is not None:
        logging.info('AWS_ACCOUNT: ' + os.getenv('AWS_ACCOUNT'))

    logging.info('')


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

    if useSession:
        try:
            if os.getenv('CONTAINERMODE') == 'true':
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

                if aws_access_key_id and aws_secret_access_key:
                    # Use the existing credentials
                    session = boto3.Session(
                        region_name=sessionRegion,  # Assuming sessionRegion is defined elsewhere
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key
                    )
                else:
                    aws_container_credentials_uri = os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
                    if aws_container_credentials_uri is None:
                        logging.error("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI environment variable is not available. "
                                      "Could not find relevant AWS credentials.")
                        sys.exit()

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
        except urllib.error.URLError as e:
            logging.error("Error accessing container credentials: " + str(e))
            sys.exit()
        except ClientError as e:
            logging.error(f"AWS ClientError: {e}")
            sys.exit("Failed to create AWS boto clients due to client error.")
        except boto3.exceptions.Boto3Error as e:
            logging.error("Boto3 error: " + str(e))
            sys.exit()
        except Exception as e:
            logging.error("An unexpected error occurred: " + str(e))
            sys.exit()
    else:
        clientSTS = boto3.client('sts', region_name=sessionRegion)
        clientEC2 = boto3.client('ec2', region_name=sessionRegion)

    return (clientSTS, clientEC2)


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
        except ClientError as e:
            if e.response['Error']['Code'] == 'UnrecognizedClientException':
                logging.error("Unrecognized AWS client. Please check your credentials.")
            else:
                logging.error(f"AWS Client Error: {e}")
            sys.exit("Failed to authenticate with AWS.")

    if os.getenv('AENV_NO_PARAMETER') == 'true':
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

        try:
            response = clientSSMMFA.get_parameters_by_path(
                Path=ssmPath,
                Recursive=True,
                WithDecryption=True
            )
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error("ClientError occurred while getting parameters by path: %s - %s", error_code, error_message)
            sys.exit()
        except Exception as e:
            logging.error("An unexpected error occurred: %s", str(e))
            sys.exit()

        verboseMode = isVerboseModeEnabled()

        if verboseMode:
            printInfo()

        for r in response['Parameters']:
            if verboseMode:
                logging.info("Loaded: SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace("/", "_").upper())
            os.environ["SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace("/", "_").upper()] = r['Value']

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
                if verboseMode:
                    logging.info("Loaded: SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace("/", "_").upper())
                os.environ["SECRET_" + os.getenv('SERVICE').upper() + r['Name'].split(os.getenv('SERVICE'))[-1].replace("/", "_").upper()] = r['Value']

    isWindows = False
    if os.name == 'nt':
        isWindows = True

    if args:
        if not isWindows:
            os.system('eval ' + '"' + ' '.join(args) + '"')
        else:
            os.system('call ' + ' '.join(args))

    if os.getenv('INTERACTIVE') == 'true':
        logging.info('Starting an interactive command-line...')
        logging.info('Environment: ' + os.getenv('ENVIRONMENT'))
        if not isWindows:
            os.system('bash')
        else:
            os.system('cmd')


def main():
    check(sys.argv[1:])

    aenvConfigPath, aenvDir, configExists = getCofigPath()

    if os.environ.get('CONTAINERMODE') is not None:
        if 'AWS_REGION' not in os.environ:
            logging.info('Container mode enabled! Please make sure to also set the region!')
            sys.exit()

    if configExists:
        aenvLoadConfig(aenvConfigRead(aenvConfigPath))

    if os.getenv('DEFAULTSERVICE') is None and os.getenv('SERVICE') is None:
        logging.info(
            "Please configure a default service with aenv -S <DEFAULTSERVICE> or provide a service with -s <SERVICE>")
        sys.exit()

    if os.getenv('OVERRIDE_ENV') is None and os.getenv('ENVIRONMENT') is None:
        logging.info("Please define an environment with aenv -e <ENVIRONMENT>.")
        sys.exit()

    app()

if __name__ == "__main__":
    main()
