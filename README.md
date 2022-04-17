# Regittable

Regittable (or reGittable) is a tool for the [reMarkable 2](https://remarkable.com/) tablet together with the [Dropbox integration](https://support.remarkable.com/hc/en-us/articles/4406214540945-Integrating-with-Google-Drive-Dropbox-and-OneDrive) using a `json` config file and run from an always-on device (or one that runs the script upon startup, see below).


## Usage options

In the simplest case, Regittable can be configured to automatically move a remarkable file after sync to a specified destination folder from your Dropbox root where it will be synced.

Note: the destination can be a Dropbox subfolder, as a workaround to the reMarkable Dropbox integration limitation where it [can only sync to the Dropbox root folder](https://www.reddit.com/r/RemarkableTablet/comments/shxbbv/is_there_a_way_to_upload_a_file_to_a_dropbox/).

It can be used to check the file directly into a git repo 

## Setup

If you will be running the `.py` file, you need to install python dependencies:
 ```
 pip install watchdog
 pip install sh
```
(a superior sub-process module for running command line calls).

## Configuration

This assumes the `regittable-config.json` file is adjacent to `regittable.py`.

Set the `db_root_rel_path` var to the absolute (or relative to the `regittable.py` location) path to your local Dropbox folder root contents.

Create a configuration object for each reMarkable notebook or file you sync to Dropbox.
```
{
  name: "quick_notes",
  destination: "./reMarkableNotes/*",
  git_mode: {"none"},
  clear: ""
}
```

Append `/*` to your destination path if you want to preserve the filename as set by your reMarkable sync. You can hard-code this filename too.

Set `git_mode` to any of 
- `pull-request`: submits a pull-request to the repo, from a branch named as in `commit-branch`.
- `commit-branch`: commits in a branch. Default branch name is of format `$filename$hhmmss$ddmmyyyy`
- `commit-current`: makes a commit in the current repo branch
- `push-current`: makes a commit and attempts a push to the current repo branch


If your computer may restart, consider setting the script to run on startup (eg: [Windows](https://stackoverflow.com/questions/4438020/how-to-start-a-python-file-while-windows-starts)).