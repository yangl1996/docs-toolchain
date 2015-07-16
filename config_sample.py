"""
Sync tool config file
"""

# Global Config
listenAddr = ""  # The address where the program is running
githubPort = 7654  # The port listening to GitHub webhook
pagurePort = 7655  # The port listening to Pagure webhook
localRepoPath = ''  # Path to the local git repository

# GitHub Part
githubSecretKey = ""  # Secret key used to sign the GitHub webhook data
githubToken = ""  # GitHub access token
githubUsername = ""  # GitHub repository admin username
githubRepo = ""  # GitHub repository name


# Pagure Part
pagureSecretKey = ""  # Secret key used to sign the Pagure webhook data
pagureToken = ""  # Pagure access token
pagureRepo = ""  # Paugre repository name

# CI Part
PID = ""
PSK = ""