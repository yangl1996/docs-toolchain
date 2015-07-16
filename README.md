# Deploying

### Get the source code

```
git clone https://github.com/yangl1996/docs-toolchain.git
cd docs-toolchain
```

### Modify ```config.py```

```
cp config_sample.py config.py
vim config.py
```

### Initialize the local git repository

1. git clone the repository on GitHub
2. add the repository on Pagure as remote ```pagure```
3. git push to ```pagure``` to ensure the three repos are identical

### Run the scripts

```
nohup python3 github.py &
nohup python3 pagure.py &
```

# Usage

1. Mirrors pull requests from GitHub Pull Request to Pagure issue
2. Syncs comments between GitHub and Pagure
3. Merges GitHub Pull Request when the relevant Pagure issue is marked as "Fixed"
4. Keeps the GitHub repo and the Pagure repo synced