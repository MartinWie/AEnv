# CredoPy aka pydo!
[![OS](https://img.shields.io/badge/Runs%20on%3A-Linux%20%7C%20Mac%20%7C%20Windows-green)]() [![RunsOn](https://img.shields.io/badge/Used%20technologies-AWS%20%7C%20Python%203-green)]() [![RunsOn](https://img.shields.io/github/license/MartinWie/CredoPy)](https://github.com/MartinWie/CredoPy/blob/master/LICENSE) [![Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)

![CredoPy aka pydo](https://github.com/MartinWie/CredoPy/blob/master/credopy_logo.png)

## Installation

* Install python3 and pip

* [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)

* Install pydo:

```
pip install credopy
```

* For YubiKey support install the [YubiKey Manager CLI](https://github.com/Yubico/yubikey-manager#installation)

* On Windows [setup Boto3 credentials](https://pypi.org/project/boto3/) 


## No passwords in code!

Make your company more secure by using the "troy password credo"! 

Easier said than done working with credentials can get very messy and lead to huge security and data protection problems. So while working at [troy gmbh](https://www.linkedin.com/company/troy-gmbh/) it became clear that we had to define some fundamental rules to maintain a high level of security during fast growth phases. This brought up the "troy password credo".

### troy password credo:
You may ask "What is the famous troy password credo?"
It's very simple: **Never** store credentials unencrypted!


## Let's get started

Working with Credentials can be fun, but from a security perspective, most of the time it isn't! Especially if you have multiple systems and different environments.

If you're using the AWS cloud you found the right repository!

Pydo is a tool that injects aws parameter store strings and secure strings into your memory as an environment variable. With this, your important credentials/security keys/... never have to touch your disk again.

And because the parameter store supports paths you can define different services with different environments.

For example:

```
/<Environment>/<KotlinApp1>/

#which could look like:
/Prod/CustomerManagement/DB/USER

#or
/Prod/CustomerManagement/DB/PASSWORD
```

Output these example data (The database password for CustomerManagement in production ):


```
pydo -e Prod -s CustomerManagement echo '$SECRET_CUSTOMERMANAGEMENT_DB_PASSWORD'
```

With both parameters, your "CustomerManagement" application/service (launched with pydo) could now access the database with the provided username and password.

Details at: [How to access the environment variables](https://github.com/MartinWie/CredoPy#how-to-access-the-environment-variables)


## Usage 

```
pydo [-s <service/application>] [-i] [-n] [-e <env>] [-t <2fa key>] [-T] [-Y] [-u <aws username>] [-a <account number>] [-p <aws profile>] [-r <region>] <command>
```

**Options:**

| Option | explination | sample | comment 
| :- | :- | :- | :-
|-h | Shows help | pydo -h |
|-i | Starts pydo in interactive mode | pydo -i | Gives you a command line that you can interact with |
|-s \<service/application> | For which service should the environment variables be loaded? | pydo -s CustomerService
|-S | Sets a default service for pydo and writes it to a config file | pydo -S CustomerService | from now on "CustomerService" is the default service which means "-s CustomerService" is redundant 
|-n | Do not query the parameter store at all  | pydo -n | Can be used to auth the current session with MFA
|-e \<env> | For which environment should the environment variables be loaded? For example Dev, Test or Prod (permission required) | pydo -e Prod | 
|-t \<2fa key> | Takes the 2FA key from your aws account | pydo -t 987123
|-T | Lets you type in the 2FA key from your aws account during runtime | pydo -T | When you run your command pydo will ask for the token |
|-Y | Uses Yubikey for MFA auth | pydo -Y | During runtime pydo will use ykman to fetch the MFA-Key from your yubikey
|-r \<region> | Overwrites temporary the awscli default region | pydo -r eu-central-1 | Pydo will use the given region for example Frankfurt
|-q | Quiet mode (less output) | pydo -q |
|-u \<aws username> | Sets a specific username combined with -a gives you a faster runtime (otherwise this data needs to be retrieved via aws) | pydo -u user@example.de |
|-a \<account number> | Sets a specific account number combined with -u gives you a faster runtime (otherwise this data needs to be retrieved via aws) | pydo -a 999999999999 | 
|-p \<aws profile> | If multiple aws profiles are available you can choose the profile otherwise pydo will use the default profile | pydo -p testUser1
|-c \<aws profile> | Container mode(enable this to make pydo work in ecs and codebuild) | pydo -c | [permissions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)
|\<command> | Is the command to execute with environment variables injected. | pydo code | Will run VS Code with access to given environment variables

Note: **It may be required to double escaping.**

Examples:

**Linux:**

pydo echo '$SECRET_CUSTOMERSERVICE_UI_URL'

or

**Windows:**

pydo echo %SECRET_CUSTOMERSERVICE_UI_URL%  

**Mac:**

pydo "/Applications/IntelliJ\ IDEA\ CE.app/Contents/MacOS/idea"

**Note** the quoting of the variable.

## Enforce MFA authentication for AWS feature / function

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
pydo -q -n -Y aws sts assume-role --role-arn "arn:aws:iam::123456789012:role/example-role" --role-session-name AWSCLI-Session

# -q removes the unnecessary output
# -n puts pydo in only authentication mode
# -Y authenticates the session with your YubiKey, alternatively you could use -t or -T
```

## Format for these environment variables:

Every environment variable that is loaded with pydo starts with "SECRET_".

Then the service-name and path, separated by underliners.

(of course in upper case)

For example: 

```
SECRET_CUSTOMERMANAGEMENT_DB_USER
```

More about environment variables: [Guide to Unix/Environment Variables](https://en.wikibooks.org/wiki/Guide_to_Unix/Environment_Variables)

This is maybe made more clear by the following example:

```
/Prod/CustomerManagement/DB/USER
```

would be accessible with:

```
SECRET_CUSTOMERMANAGEMENT_DB_USER
```

or

```
/Prod/CustomerManagement/DB/PASSWORD
```

would be accessible with:

```
SECRET_CUSTOMERMANAGEMENT_DB_PASSWORD
```

## Environments

We now talked a lot about environments, but how can pydo differ between different environments like dev, test, or prod?

Quite simply, you tell it!

**Parameterstore:**

As already mentioned you Define the environment as the first section.

Let's take the previous example:

```
/Prod/CustomerManagement/DB/PASSWORD
```

here "Prod" is our environment for the database(DB) password (PASSWORD) of our CustomerManagement service/application, but we could easily also set this for our test environment like this:

```
/Test/CustomerManagement/DB/PASSWORD
```

(When creating new parameters don't forget to create them as "SecureString's" ;) )

Bonus content: 

Converting parameter store strings to secure strings
Found this in my old files, before using this **test and make sure it really works** but with this snippet, you should be able to convert every normal parameter store string to a secure string.

**No guarantee for functionality, make sure you have a backup of the parameter store variables**

```
import boto3
client = boto3.client('ssm')
response = client.describe_parameters()
nameList = []
dic = {}
dic_descr = {}

for p in response['Parameters']:
    nameList.append(p['Name'])
    dic_descr[p['Name']] = p.get('Description')

nextToken_Str = response['NextToken']

while nextToken_Str:
    response = client.describe_parameters(NextToken=nextToken_Str)
    
    for p in response['Parameters']:
        nameList.append(p['Name'])
        dic_descr[p['Name']] = p.get('Description')
    
    nextToken_Str = response.get('NextToken', None)
        
for name in nameList:
    response = client.get_parameter(Name=name, WithDecryption=True)
    dic[name] = response.get('Parameter').get('Value')


for name in dic:
    if dic_descr[name] is not None:
        print(client.put_parameter(
            Name=name,
            Description=dic_descr[name],
            Value=dic[name],
            Type='SecureString',
            Overwrite=True
        ))
    else:
        print(client.put_parameter(
            Name=name,
            Value=dic[name],
            Type='SecureString',
            Overwrite=True
        ))

```

**Client/You**

With

```
pydo -e <env>
```

you can launch pydo for every in the parameterstore defined environment.

If you don't set any pydo swtiches to "Dev"

**AWS Server**

when pydo runs on an aws machine you could run it with "-e \<env>" but this is rather inconvenient. So pydo queries the instance tags and searches for the key "environment" and uses its value as the current environment. If the environment tag is not set and you did not provide an environment with "-e" pydo automatically defaults to "Dev"


## How to access the environment variables

To access those environment variables you have to run your application/service with pydo.

```
pydo java -jar service.jar
//or
pydo python service2.py
```

Now these two services have all environment variables for their service and environment available and can work with them here are two easy examples:

**Python:**

```
import os
os.getenv('SECRET_CUSTOMERMANAGEMENT_DB_PASSWORD')

#or let's say you want to fetch an API, but need an API token in a header request:
....

header = { 'Api-Key' : os.getenv('SECRET_CUSTOMERMANAGEMENT_API_KEY') }
....

```

**Kotlin:**

```
val envVar : String? = System.getenv("varname")
//there are some other examples feel free to look into https://stackoverflow.com/ but I like this approach because environment variables can be null, bus null handling probably comes down to your use-case/coding style.
```

## Authentication

**AWS Server:**

Easy!
Done by boto3 automatically uses in instance role defined permissions.

(Details "Permissions" section)

**Developer:**

boto3 uses the aws CLI's authentication so make sure you set this up before ;)

[AWS CLI](https://aws.amazon.com/cli/)

By default, pydo uses the aws CLI default profile, but of course, you can choose the profile, that you want to use, simply do:

```
pydo -p <awscli profile name>
#or 
pydo -h 
#to see more configuration options
```

(More details in the "Usage" section)

**MFA**

First of all multi-factor authentication is highly suggested!

https://lmgtfy.com/?q=why+mfa+is+important

Ok, all jokes aside especially for production parameters your IAM users should require MFA authentication at least for production parameters.

So even when a password/account from one of your users gets compromised and let's be realistic here, this will definitely happen to your company/project so better prepare for that event!

"How can we mitigate the damage" 

At least in my humble opinion, this should be a "better be safe than sorry" point.

Especially for your production systems!

Pydo supports multiple MFA options, details in the "Usage" section, here the short overview:

```
# normal virtual mfa token:
pydo -t <TOKEN>

#askt for the token during runtime:
pydo -T

# leads to:
$ pydo -T
$ Please enter token: 

#Yubikey Authenticator:
pydo -Y

```

At the moment aws-CLI only supports virtual MFA devices(so the -Y option uses the virtual MFA function of your yubikey (ykman) as a workaround until awscli supports hardware tokens ), but feel free to drop a comment or investigate here:

https://github.com/aws/aws-cli/issues/3607


## Permissions: IAM policies / Instance roles

| Permission | Used in the code | Documentation | Comment 
| :- | :- | :- | :-
| "ec2:DescribeTags" | clientEC2.describe_tags() | https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeTags.html |
| "sts:GetCallerIdentity" | clientSTS.get_caller_identity() | https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html | Optional(No permissions are required to perform this operation.)
| "sts:GetSessionToken" | clientSTS.get_session_token() | https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html |
| "ssm:GetParametersByPath" | clientSSMMFA.get_parameters_by_path() | https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html |
| "iam:ListMFADevices" | boto3.client('iam').list_mfa_devices() | https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_iam_mfa-selfmanage.html | Optional! (At the moment not in use but as soon aws API supports hardware tokens this can be enabled to let pydo support hardware MFA's) 

**tldr Minimal permissions:**

“ec2:DescribeTags”

“sts:GetSessionToken”

“ssm:GetParametersByPath”

## Setup

1. Define environment variables as described in **Format for these environment variables**
2. Set environment tag's for your instances as described in **AWS Server**
3. Create/adjust your instance roles/IAM roles with proper permissions as described in 

**Permissions**

## Todo

* document how to enforce MFA / pydo for only prod env variables
* Load service name also from aws tags
* Add more information about container mode and necessary IAM permissions
* Enhance local profile/config setup/usage
* Load multiple services at once instead of concatenating multiple pydo calls ( "pydo -s Service1 pydo -s Service2 ")
 * Load environment tags for ECS container / for task
* feature to refresh env variables in the background
* Add testing https://pydantic-docs.helpmanual.io/
* Add feature for only loading certain variables to speed up loading

## Acknowledgments 

**Inspired by:**

* **Gunnar Zarncke** - [LinkedIn](https://www.linkedin.com/in/gunnar-zarncke-952134163/) and his/troy gmbh's opensource credo projekt - [Git Credo](https://bitbucket.org/infomadis/troy-credo-aws/)

**Bug reports:**

* **[Arif PEHLİVAN](https://github.com/mrpehlivan)** 

* **[Carlos Freund](https://github.com/happyherp)**


## Donations

If you want to tip me or simply want to say thanks:

[Paypal](https://www.paypal.me/MartinWiechmann)


## License

MIT [Link](https://github.com/MartinWie/CredoPy/blob/master/LICENSE)

## Support me :heart: :star: :money_with_wings:
If this project provided value, and you want to give something back, you can give the repo a star or support by making buying me a coffee.

<a href="https://buymeacoffee.com/MartinWie" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" width="170"></a>
