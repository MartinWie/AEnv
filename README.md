# AEnv

[![OS](https://img.shields.io/badge/Runs%20on%3A-Linux%20%7C%20Mac%20%7C%20Windows-green)]() [![RunsOn](https://img.shields.io/badge/Used%20technologies-AWS%20%7C%20Python%203-green)]() [![RunsOn](https://img.shields.io/github/license/MartinWie/AEnv)](https://github.com/MartinWie/AEnv/blob/master/LICENSE) [![Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)

![AEnv](https://github.com/MartinWie/AEnv/blob/master/AEnv_logo.png)

A Python-based CLI tool to simplify the process of fetching and injecting environment variables from AWS Parameter Store.

## Table of Contents

1. [Description](#description)
2. [Installation](#installation)
3. [Usage](#Usage)
4. [Setup](#Setup)
5. [Permissions](#Permissions)
6. [Concept](#Concept)
7. [Access-parameter-store-entries](#Access-parameter-store-entries)
8. [Authentication](#Authentication)
9. [Todos](#Todos)
10. [Acknowledgments](#Acknowledgments)
11. [License](#License)

## Description

This CLI tool (`aenv`) allows you to fetch environment variables from AWS Parameter Store, injecting them into your local environment for use in your applications. The tool also supports authentication with MFA, including Yubikeys.



## Installation

### Prerequisites

* Install python3 and pip

* [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
* Boto3 (Will be installed with the aenv package)
  * Windows: [setup Boto3 credentials](https://pypi.org/project/boto3/)


### Main Package (aenv)

```
pip install aenv
```



## Usage

```
aenv --help
# or
aenv -h
```

All current options:
```
aenv [-s <service/application>] [-i] [-n] [-e <env>] [-t <2fa key>] [-T] [-Y] [-u <aws username>] [-a <account number>] [-p <aws profile>] [-r <region>] <command>
```

| Option | Explanation | Sample | Comment |
| ------ | ----------- | ------ | ------- |
| -h | Shows help | `aenv -h` | |
| -i | Starts aenv in interactive mode | `aenv -i` | Gives you a command line that you can interact with |
| -s \<service/application> | For which service should the environment variables be loaded? | `aenv -s CustomerService` | |
| -S | Sets a default service for aenv and writes it to a config file | `aenv -S CustomerService` | from now on "CustomerService" is the default service which means "-s CustomerService" is redundant |
| -n | Do not query the parameter store at all  | `aenv -n` | Can be used to auth the current session with MFA |
| -e \<env> | For which environment should the environment variables be loaded? For example Dev, Test or Prod (permission required) | `aenv -e Prod` | |
| -t \<2fa key> | Takes the 2FA key from your aws account | `aenv -t 987123` | |
| -T | Lets you type in the 2FA key from your aws account during runtime | `aenv -T` | When you run your command aenv will ask for the token |
| -Y | Uses Yubikey for MFA auth | `aenv -Y` | During runtime aenv will use ykman to fetch the MFA-Key from your yubikey |
| -r \<region> | Overwrites temporary the awscli default region | `aenv -r eu-central-1` | aenv will use the given region for example Frankfurt |
| -v | Verbose mode (more output) | `aenv -v` | |
| -u \<aws username> | Sets a specific username combined with -a gives you a faster runtime (otherwise this data needs to be retrieved via aws) | `aenv -u user@example.de` | |
| -a \<account number> | Sets a specific account number combined with -u gives you a faster runtime (otherwise this data needs to be retrieved via aws) | `aenv -a 999999999999` | |
| -p \<aws profile> | If multiple aws profiles are available you can choose the profile otherwise aenv will use the default profile | `aenv -p testUser1` | |
| -c \<aws profile> | Container mode(enable this to make aenv work in ecs and codebuild) | `aenv -c` | [permissions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html) |
| \<command> | Is the command to execute with environment variables injected. | `aenv code` | Will run VS Code with access to given environment variables |



## Setup

Lets start with setting up a simple example service. Let's call it **UserService**. 

The **UserService** needs a **database hostname**, a **database username** and a **database password**. 

Let's assume, we have two environments, "Dev" and "Test" and we want to inject the correct **UserService**,  **database hostname**,... for the related environment.

Step 1 is to create the AWS parameter store entries.
Let's create two entries:

```
/Dev/UserService/DB/hostname
# and 
/Test/UserService/DB/hostname
```

Both are SecureString, that hold the values:
```
db.dev.example.com for /Dev/UserService/DB/hostname
and
db.test.example.com for /Test/UserService/DB/hostname
```

Step 2 is to fetch those values and have them available as environment variables.

For the **UserService** variables on Dev run:

```
aenv -e Dev -s UserService 
```
This command fetches all entries from the parameter store with the path /Dev/UserService/* and makes them available as environment variables.

If you just want to echo out the DB hostname we created (/Dev/UserService/DB/hostname) you can run:

```
aenv -e Dev -s UserService echo '$SECRET_USERSERVICE_DB_HOSTNAME'
```

You can also run your service with aenv to have the correct DB hostname available in the service as an environment variable.
The call for a Python or JVM service would be:

```
aenv -e Dev -s UserService java -jar service.jar
# or
aenv -e Dev -s UserService python service2.py
```

Both services now have access to the environment variable "SECRET_USERSERVICE_DB_HOSTNAME" containing the value that we defined for "/Dev/UserService/DB/hostname".

## Permissions

### Permissions (User)

Here is the minimal suggested set of IAM permissions to use aenv for all services that can be found for our Dev environment:

(Do not forget to adapt to account ID(123456789098) to your own )  

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParametersByPath",
                "ssm:GetParameters",
                "ssm:ListTagsForResource",
                "ssm:GetParameter"
            ],
            "Resource": [
                "arn:aws:ssm:*:123456789098:parameter/Dev/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "ssm:DescribeParameters",
            "Resource": "*"
        }
    ]
}
```
These permissions allow to fetch all entries for any service in the Dev environment.

For example, fetching all environment variables for a service called UserService:

```
aenv -e Dev -s UserService
```

To further limit access to only allow loading environment variables for a specific service like "UserService" we need to adapt the "Resource":

```
"Resource": [
                "arn:aws:ssm:*:123456789098:parameter/Dev/UserService/*"
            ]
```



#### Permissions (AWS)

This is a work in progress!

Currently, the yubikey needs to be added as a **virtual mfa** and needs to be the **first** device in our Multi-factor authentication devices.
Feel free to also add your Yubikey as a hardware mfa **afterwards**.(The AWS web console works flawless with multiple mfa's)

```
pip install --user yubikey-manager
```
[Official documentation](https://docs.yubico.com/software/yubikey/tools/ykman/Install_ykman.html)


## Permissions (IAM policies / Instance roles)

| Permission | Used in the code | Documentation | Comment 
| :- | :- | :- | :-
| "ec2:DescribeTags" | clientEC2.describe_tags() | https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeTags.html |
| "sts:GetCallerIdentity" | clientSTS.get_caller_identity() | https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html | Optional(No permissions are required to perform this operation.)
| "sts:GetSessionToken" | clientSTS.get_session_token() | https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html |
| "ssm:GetParametersByPath" | clientSSMMFA.get_parameters_by_path() | https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html |
| "iam:ListMFADevices" | boto3.client('iam').list_mfa_devices() | https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_iam_mfa-selfmanage.html | Optional! (At the moment not in use but as soon aws API supports hardware tokens this can be enabled to let aenv support hardware MFA's) 

**tldr Minimal permissions:**

“ec2:DescribeTags”

“sts:GetSessionToken”

“ssm:GetParametersByPath”

### Advanced permission 1 (Enforce MFA authentication for accessing Prod parameters)

To enforce MFA authentication for all Prod parameters you can make use of the condition "MultiFactorAuthPresent" in your IAM permission.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ssm:PutParameter",
                "ssm:DeleteParameter",
                "ssm:GetParameterHistory",
                "ssm:GetParametersByPath",
                "ssm:GetParameters",
                "ssm:ListTagsForResource",
                "ssm:GetParameter",
                "ssm:DeleteParameters"
            ],
            "Resource": [
                "arn:aws:ssm:*:123456789098:parameter/Prod/*"
            ],
            "Condition": {
                "Bool": {
                    "aws:MultiFactorAuthPresent": "true"
                }
            }
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "ssm:DescribeParameters",
            "Resource": "*"
        }
    ]
}
```

### Advanced permission 2 (Enforce MFA authentication for AWS feature / function)

Add the condition "MultiFactorAuthPresent" to your IAM permission:

```
    "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}}
```

Sample for sts:AssumeRole: 

```
{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Principal": {"AWS": "ACCOUNT-B-ID"},
    "Action": "sts:AssumeRole",
    "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}}
  }
}
```

Now you need MFA authentication to run assume role commands.
Sample call for this would be:

```
aenv -v -n -Y aws sts assume-role --role-arn "arn:aws:iam::123456789012:role/example-role" --role-session-name AWSCLI-Session

# -v enables verbose mode
# -n puts aenv in only authentication mode
# -Y authenticates the session with your YubiKey, alternatively you could use -t or -T
```


## Concept

AEnv uses the parameter store path to define the environment and service name, following this schema:

```
/<Environment>/<Service-Name>/

# Which could look like:
/Prod/CustomerManagement/DB/USER
# Or
/Prod/CustomerManagement/DB/PASSWORD
```

Having those two in place would enable our **CustomerManagement** service running in our Prod environment to access, the environment variables:
SECRET_CUSTOMERMANAGEMENT_DB_USER
and 
SECRET_CUSTOMERMANAGEMENT_DB_PASSWORD

With both parameters in place, your **CustomerManagement** application/service, launched with aenv, could now access the database with the provided username and password.

```
aenv -e Prod -s CustomerManagement java -jar service.jar
```

#### Format for these environment variables:

Every environment variable that is loaded with aenv starts with "SECRET_".

Then the service-name and path, separated by underliners. (of course in upper case)

For example: 

```
/Prod/CustomerManagement/DB/USER
```

would be accessible with:

```
SECRET_CUSTOMERMANAGEMENT_DB_USER
```

or

```
/Prod/CustomerManagement/DB/PASSWORD/USER1
```

would be accessible with:

```
SECRET_CUSTOMERMANAGEMENT_DB_PASSWORD_USER1
```

More about environment variables: [Guide to Unix/Environment Variables](https://en.wikibooks.org/wiki/Guide_to_Unix/Environment_Variables)


## Access-parameter-store-entries

#### Testing single variables
**Linux/Mac**

```
aenv -e Dev -s UserService echo '$SECRET_USERSERVICE_UI_URL'
```

or

**Windows**

```
aenv -e Dev -s UserService echo %SECRET_USERSERVICE_UI_URL%  
```


### How to access the environment variables in Kotlin and Python

#### How to access the environment variables

To access those environment variables you have to run your application/service with aenv.

```
aenv -e Dev -s UserService java -jar service.jar
//or
aenv -e Dev -s UserService python service2.py
```

Now these two services have access to all Dev environment variables for the UserService.
Here are easy examples for Python and Kotlin:

**Python:**

```
import os
os.getenv('SECRET_USERSERVICE_HOSTNAME')

# For example conneting to a host depending on the environment:
....

hostname = os.getenv('SECRET_USERSERVICE_HOSTNAME')
....

```

**Kotlin:**

```
val envVar : String? = System.getenv("SECRET_USERSERVICE_HOSTNAME")
```

### Bonus:
#### Running a local application with access to environment variables of a given service

Linux/Mac running IntelliJ with Test environment variables for the **UserService**

```
aenv -e Test -s UserService "/Applications/IntelliJ\ IDEA\ CE.app/Contents/MacOS/idea"
```

This can come in handy if you want to debug something that only seems to occure in the Test environment. 



## Authentication

**AWS Server:**

Easy!

Done by boto3. Boto3 automatically uses the in the instance role defined permissions.

(Details "Permissions" section)

**Developer:**

boto3 uses the aws CLI's authentication so make sure you set this up before ;)

[AWS CLI](https://aws.amazon.com/cli/)

By default, aenv uses the aws CLI default profile, but of course, you can choose the profile, that you want to use, simply do:

```
aenv -p <awscli profile name>
#or 
aenv -h 
#to see more configuration options
```

(More details in the "Usage" section)

**MFA**

Multi-factor authentication is highly suggested!

https://lmgtfy.com/?q=why+mfa+is+important

Ok, all jokes aside especially for production parameters your IAM users should require MFA authentication at least for production parameters.

At least in my humble opinion, this should be a "better be safe than sorry" point.

Especially for your production systems!

AEnv supports multiple MFA options, details in the "Usage" section, here the short overview:

```
# Normal virtual mfa token:
aenv -t <TOKEN>

# Asks for the token during runtime:
aenv -T

# leads to an interactive token query during runtime:
$ aenv -T
$ Please enter token: 

#Yubikey Authenticator:
aenv -Y

```

## Todos

* Add managing mode with TerminalMenu to read specific values 
  * Function to add new entries
  * Function to update existing entries
  * Function to delete existing entries
* refactor whole code base
* Add better permission error handling (Especially the auth part with Yubikey handling)
* Add check if service exists/can be read with proper error message
* Update and correct -h / --help output
* Add regex filter for only loading specific variables
* Add regex filter to leave out variables from loading
* add -P to save a default profile
* Update initial setup instructions + console output for this(ykman + output for missing service)
* Option to list all available environments / services(discover/list env / list services)
* Check for ykman on -Y calls improve output
* Currently only the fist MFA device of any given account is used -> add mfa device selection + option for default selection
* cleanup/refactor documentation / improve overall structure
* add auth only mode(no env and no service name given)
* Add more information about container mode and necessary IAM permissions
* Enhance local profile/config setup/usage
* Handle the region in the same way services are handled
* Load multiple services at once instead of concatenating multiple aenv calls ( "aenv -s Service1 aenv -s Service2 ")
* Add feature for only loading certain variables to speed up loading
* Add assume role feature to support this setup more ease -> https://aws.amazon.com/de/blogs/security/enhance-programmatic-access-for-iam-users-using-yubikey-for-multi-factor-authentication/
* Add testing

## Acknowledgments 

**Inspired by:**

* **Gunnar Zarncke** - [LinkedIn](https://www.linkedin.com/in/gunnar-zarncke-952134163/) and his/troy gmbh's opensource credo projekt - [Git Credo](https://bitbucket.org/infomadis/troy-credo-aws/)

**Bug reports:**

* **[Arif PEHLİVAN](https://github.com/mrpehlivan)** 

* **[Carlos Freund](https://github.com/happyherp)**

## License

MIT [Link](https://github.com/MartinWie/AEnv/blob/master/LICENSE)

## Support me :heart: :star: :money_with_wings:
If this project provided value, and you want to give something back, you can give the repo a star or support by buying me a coffee.

<a href="https://buymeacoffee.com/MartinWie" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" width="170"></a>
