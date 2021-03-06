#!/usr/bin/python
import os, sys
import pygit2 as git
import hashlib, shutil, keyring
import json as jsoner
from raptor_codescan import *
from raptor_externalscan import *

rulepacks = ['common', 'android', 'php', 'actionscript']

json = { 
		"scan_info": {
		"app_path": "",
		"security_warnings": "",
		"start_time": "",
		"end_time": "",
		"duration": "",
		"version": "0.0.1"
	},
	"warnings": [],
	"ignored_warnings": [],
	"errors": []
}

def scan_all(scan_path, repo_path):
	counter_start = time.clock()
	
	results = []
	js_results = []
	ror_results = []
	php_results = []
	total_issues = 0

	start_time = time.strftime("%a, %d %b %Y %I:%M:%S %p", time.localtime())

	for index in range(0,len(rulepacks)):
		rule_path = 'rules/%s.rulepack' % rulepacks[index]
		report_path = scan_path + '/%s_report.json' % rulepacks[index]
		result = Scanner(scan_path, rule_path, report_path)

		if len(result.issues) > 0:
			for issue in result.issues:
				results.append(issue)
				total_issues += 1

	print "[INFO] Started scanjs plugin"
	js_results = scanjs(scan_path)
	if len(js_results) > 0 and js_results != 'error':
		for js_issue in js_results:
			results.append(js_issue)
			total_issues += 1
	
	print "[INFO] Started brakeman plugin"
	ror_results = scan_brakeman(scan_path)
	if len(ror_results) > 0 and ror_results != 'error':
		for ror_result in ror_results:
			results.append(ror_result)
			total_issues += 1

	print "[INFO] Started rips plugin"
	php_results = scan_phprips(scan_path)
	if len(php_results) > 0 and php_results != 'error':
		for php_result in php_results:
			results.append(php_result)
			total_issues += 1

	counter_end = time.clock()
	json["scan_info"]["app_path"] = repo_path
	json["scan_info"]["security_warnings"] = total_issues
	json["scan_info"]["start_time"] = start_time
	json["scan_info"]["end_time"] = time.strftime("%a, %d %b %Y %I:%M:%S %p", time.localtime())
	json["scan_info"]["duration"] = str(counter_end - counter_start)
	json["scan_info"]["version"] = "0.0.1"
	json["warnings"] = results
	json["ignored_warnings"] = ""
	json["errors"] = ""
	return json

def clone(repo_name, internal):
	uniq_path = hashlib.sha224(repo_name).hexdigest()

	uniq_path = hashlib.sha224(repo_name).hexdigest()
	if os.path.isdir(os.getcwd() + '/clones/' + uniq_path):
		shutil.rmtree(os.getcwd() + '/clones/' + uniq_path)

	repo_url = 'https://github.com/%s.git' % (repo_name)

	try:
		clone_dir = os.getcwd() + '/clones/'
		if not os.path.isdir(clone_dir):
			os.makedirs(clone_dir)
		repo_path = clone_dir + uniq_path
		login_info = ''
		if internal==True:
			username = 'dpnishant' #your-github-username-here
			password = str(keyring.get_password('github', username))
			login_info = git.UserPass(username, password)
		git_obj = git.clone_repository(repo_url, repo_path, credentials=login_info)			
		return repo_path
	except Exception, e:
		print e
		if str(e).find('Unexpected HTTP status code: 404'):
			print "Repo doesn't exists"
			return "Repo doesn't exists"
		#return str(e)

def delete_residue(path, report_files):
	shutil.rmtree(path)

def start(repo_path, report_dir, internal):
	print "==============New Scan==================="
	print "[INFO] Now cloning: %s" % (repo_path)
	cloned_path = clone(repo_path, internal)
	if os.path.isdir(cloned_path):
		print "[INFO] Now scanning: %s" % repo_path
		results = scan_all(cloned_path, repo_path)
		print "[INFO] Scan complete! Deleting repo..."
		delete_residue(cloned_path, rulepacks)
		return results
