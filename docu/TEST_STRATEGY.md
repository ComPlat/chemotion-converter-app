# Test Strategy

This document details the test strategy that has been implemented for the converter project. 
The initial section provides a detailed overview of the blackbox testing process for the 
profiles and readers. The second section provides a detailed explanation of the toolkit 
provided with this repository, which facilitates test-driven development of new readers.


Before continuing please check if your Python setup fits [Setup Python](## Setup Python Virtual Environment)

## Blackbox testing 

All published [reader](https://chemotion.net/docs/services/chemconverter/readers) and
[profiles](https://chemotion.net/docs/services/chemconverter/profiles) are currently 
undergoing black box testing. 

To use the Test Manager, cd into the project directory and run:

```shell
python -m test_manager [-h] [-e] [-ep] [-t] [-tp] [-g]
```

### Help

Get a brief docu:  

```shell
python -m test_manager -h
```

###  Download test files

To get all the profiles and test files from GitHub, just run:

```shell
python -m test_manager -g
```

It fetches the profiles and test files from the added_data_files branch of the repository: https://github.com/ComPlat/chemotion_saurus.git

###  Generate black box tests

Generate files:  

```shell
python -m test_manager -t -tp
```

This generates two files:

- test_manager/test_profiles.py
- test_manager/test_readers.py

### Overwrites expected test results

To overwrite the expected test results run:

```shell
python -m test_manager -e -ep
```


This generates a directory test_manager/profile_results and a directory test_manager/reader_results.

> [!CAUTION]
> Make sure that you check the changes in the git diff before you commit the results of this command.
> If you commit false changes it may permanently falsify the test results!

> [!TIP]
> This is a prerequisite if you have modified an existing reader or updated the version of the converter. In such cases, the tests are likely to fail and the expected results will need to be updated.

### All Options

| Short | Long | Help |
| ---    | ---   | ---     |
| -h | --help | show this help message and exit |
| -e | --expected | Overwrites expected test results for reader tests. Be careful. May permanently falsify the test results! |
| -ep | --expected_profiles | Overwrites expected test results for profile tests. Be careful. May permanently falsify the test results! |
| -t | --tests | Generates all reader tests in: test_readers.py |
| -tp | --test_profiles | Generates all profile tests in: test_profiles.py |
| -g | --github | Reloads profiles and test files from the Git Repository: https://github.com/ComPlat/chemotion_saurus.git branch=added_data_files |


### Run tests:

```shell
pytest .
```

## Test Drive Develop 

You can simply develop a new reader by running the following command:

```shell
python -m converter_app new_reader -n [READER_NAME] -p [PRIORITY] -t [TEST_FILE]
```

- replace \[READER_NAME\] with the name of the reader in CamelCase.
- replace \[PRIORITY\] with the priority of the reader. The lower the number, the earlier the reader is checked. Therefore, the probability that it will be used increases!
  -profile PROFILE      A test Profile if existing!
- replace \[TEST_FILE\] with the path to a test file for test drive development!

This command performs the following functions:

-	It creates a new reader in the _converter_app/reader_ directory.
-	It copies the test file into _test_static/test_files_.
-	It creates a new test script in _test_static_.

It is now possible to define the metadata and data you expect in the test cases in the test script, and develop the reader from there.

## Setup Python Virtual Environment

#### 1. Create a Virtual Environment

In your project directory, run:

```shell
python -m venv venv
```

- venv is the name of the virtual environment folder (you can name it anything).
- This command creates an isolated Python environment.

#### 2. Activate the Virtual Environment

On Linux / macOS:

```shell
source venv/bin/activate
```

On Windows (CMD):

```shell
venv\Scripts\activate
```

On Windows (PowerShell):

```shell
venv\Scripts\Activate.ps1
```

After activation, your terminal prompt should change, showing the virtual environment name.

#### 3. Install Dependencies

Once the environment is activated, install the required packages:

```shell
pip install -r requirements/dev.txt
```

This reads the requirements.txt file and installs all listed Python packages into the virtual environment.

#### Step 1-3

```shell
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements/dev.txt
```