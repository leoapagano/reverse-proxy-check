import difflib
import socket
from urllib.parse import urlparse

import requests
import urllib3


def is_url(string):
	"""Check if a string is a fully formed URL."""
	try:
		result = urlparse(string)
		return all([result.scheme, result.netloc])
	except ValueError:
		return False


def get_base_url(url):
	"""Given some URL, of the form 'http://example.com/page/page',
	get_base_url() will return 'http://example.com'."""
	parsed = urlparse(url)
	return f"{parsed.scheme}://{parsed.netloc}"


def get_ipv4_addrs(domain):
	"""Given a domain name, returns a list containing all IPv4 addresses
	which the domain resolves to."""
	try:
		return socket.gethostbyname_ex(domain)[2]
	except Exception as e:
		print(f"ERROR: Failed to resolve {domain}: {e}")
		return None


def resolve_redirects(url):
	"""Given a URL, returns the URL it redirects to.
	If the URL does not redirect, this will just return the URL fed to it."""
	try:
		resp = requests.head(url, timeout=10, allow_redirects=False, verify=False)
	except Exception as e:
		print(f"ERROR: Request to {url} failed: {e}")
		return url

	if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
		# Determine location to redirect to
		location = resp.headers.get("Location")
		if not is_url(location):
			# Needed if location is a subpage on the same domain
			location = f"{get_base_url(url)}{location}"

		return resolve_redirects(location)
	else:
		return url


def fetch(url):
	"""Fetches the contents stored at a URL and returns it as a string.
	Will return None if this fails."""
	try:
		response = requests.get(url, timeout=10, verify=False)
		return response
	except Exception as e:
		print(f"ERROR: Request to {url} failed: {e}")
		return None


def compare_strings(str1, str2):
	"""Given two strings str1 and str2, compare_strings() compares them.
	Returns the ratio of how much they match each other.
	0.0 = no match, 0.7 = possible match, 1.0 = perfect match."""
	return difflib.SequenceMatcher(None, str1.text.strip(), str2.text.strip()).ratio()


def check_reverse_proxy(domain):
	"""Check if a domain sits behind a reverse proxy or not.
	If you type a domain and its IP address into two websites, comparing them,
	they'll return the same webpage if it does not use a CDN or reverse proxy,
	or a different page if they do use one (i.e. Fastly or Cloudflare).
	Returns a ratio, where higher values = lower chance of reverse proxy."""
	ips = get_ipv4_addrs(domain)
	if ips is None:
		return -1

	# Resolve domain name to URL and fetch it
	url_domain = f"http://{domain}"
	resolved_url_domain = resolve_redirects(url_domain)
	domain_contents = fetch(resolved_url_domain)
	if domain_contents is None:
		return -1

	# Resolve each IP address to a final URL
	max_similarity_ratio = -1
	max_similarity_ip = ""
	for ip in ips:
		# Resolve IP to URL
		url_ip = f"http://{ip}"
		resolved_url_ip = resolve_redirects(url_ip)

		# Initial check: does this include the original domain?
		# If so most likely does NOT use a reverse proxy
		if domain in resolved_url_ip:
			return 1.0

		# Otherwise, fetch and find the max similarity ratio
		ip_contents = fetch(resolved_url_ip)
		if ip_contents is None:
			continue
		similarity_ratio = compare_strings(domain_contents, ip_contents)
		if similarity_ratio > max_similarity_ratio:
			max_similarity_ip = ip
			max_similarity_ratio = similarity_ratio

	if max_similarity_ip:
		print(f"IP with greatest similarity: {max_similarity_ip}")
	return max_similarity_ratio


# Example usage
if __name__ == "__main__":
	# Hide verbose output
	urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

	# Get target domains
	print("=== REVERSE PROXY CHECKER ===")
	print("Enter target domain(s), separated by spaces:")
	target_domains = input().split()

	# Check each domain
	yes_domains = []
	no_domains = []
	for domain in target_domains:
		print(f"=== {domain} ===")
		result = check_reverse_proxy(domain)
		if result == -1:
			print("FAILED TO RESOLVE DOMAIN\n")
		elif result >= 0.99:
			print("NOT BEHIND REVERSE PROXY OR CDN\n")
			no_domains.append(domain)
		else:
			if result >= 0.7:
				print("PROBABLY NOT BEHIND REVERSE PROXY OR CDN")
				no_domains.append(domain)
			else:
				print("MOST LIKELY BEHIND REVERSE PROXY OR CDN")
				yes_domains.append(domain)
			print(f"ODDS OF USING A REVERSE PROXY/CDN: {round((1-result)*10000)/100}%\n")

	# Print summary
	print("=== SUMMARY ===")

	print("The following domains are NOT using CDNs or reverse proxies:")
	if no_domains:
		for domain in no_domains:
			print(f" - {domain}")
	else:
		print("NONE")

	print("And the following domains are:")
	if no_domains:
		for domain in yes_domains:
			print(f" - {domain}")
	else:
		print("NONE")
