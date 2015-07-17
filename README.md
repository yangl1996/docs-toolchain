# Deploying

### Get the requirements

- requests
- libpagure
- markdown
- urllib

You may use pip to install modules above.

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

### CI Server
1. Set up CI repo
2. Start HTTP server on that repo

### Run the scripts

```
nohup python3 github.py &
nohup python3 pagure.py &
```

# Usage

1. Mirrors pull requests from GitHub Pull Request to Pagure issue
2. Syncs comments between GitHub and Pagure
3. Continuously Integrates (CI) with ability to preview the changed documents
4. Merges GitHub Pull Request when the relevant Pagure issue is marked as "Fixed"
5. Keeps the GitHub repo and the Pagure repo synced