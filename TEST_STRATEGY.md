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

Get a brief docu:  

```shell
python -m test_manager -t -tp
```

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
pip install -r requirements.txt
```

This reads the requirements.txt file and installs all listed Python packages into the virtual environment.

#### Step 1-3

```shell
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```