"""
SITEMAP GENERATOR - Setup for Git Hooks (Auto-run on every push)
----------------------------------------------------------------
License: AGPL-3.0 (https://www.gnu.org/licenses/agpl-3.0.html)
Website: https://bemozi.github.io
Source:  https://github.com/bemozi/Sitemap-Generator
Contact: @StatimGlobal (Twitter/X)

1. REMOTE (GitHub Actions): Replaces traditional 'post-receive' hooks.
   - Create '.github/workflows/sitemap.yml' to run the script on every push
   - Use 'actions/checkout@v4' with 'fetch-depth: 0' to ensure accurate dates.

2. LOCAL (Pre-Push): Best for local developers.
   - Create '.git/hooks/pre-push' with:
     #!/bin/sh
     python3 sitemap_generator.py && git add sitemap.xml && git commit -m "sitemap" --no-verify || true
   - Run: chmod +x .git/hooks/pre-push
"""

import os, subprocess, html, argparse
from datetime import datetime

def calculate_crawl_frequency(file_iso_date, repo_latest_iso_date):
    try:
        lastmod = (datetime.strptime(repo_latest_iso_date, '%Y-%m-%d') - datetime.strptime(file_iso_date, '%Y-%m-%d')).days
        return 'daily' if lastmod < 7 else 'weekly' if lastmod < 30 else 'monthly' if lastmod < 365 else 'yearly'
    except:
        return 'monthly'
Would you like me to tweak the Python script itself to be more efficient (for example, by caching the Git results)?
def generate_sitemap(
    url=None,
    include=('*.ht*',),
    exclude=('404.ht*', '.github/*', 'automations/*', 'feeds/*'),
    strip_index=None
):
    if url is None:
        url = f'https://{os.getenv("GITHUB_REPOSITORY_OWNER", "bemozi").lower()}.github.io'
    else:
        url = url.rstrip('/')
    repo_latest_iso_date = subprocess.check_output(['git', 'log', '-1', '--format=%as'], text=True).strip()
    git_command = [
        'git', 'ls-files',
        '--format=%(objectname:short=0) %(commitdate:iso8601) %(path)',
        ':(exclude)sitemap.xml'
    ]
    git_command.extend(include)
    for excluded in exclude:
        git_command.append(f':(exclude){excluded}')
    git_process = subprocess.Popen(git_command, stdout=subprocess.PIPE, text=True)
    if strip_index:
        strip_index = tuple(sorted(strip_index, key=len, reverse=True))
    with open(os.path.join(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip(), 'sitemap.xml'), 'w', encoding='utf-8', newline='\n') as sitemap_file:
        sitemap_file.write(f'''\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:gh="{url}/metadata">
''')
        for line in git_process.stdout:
            git_metadata = line.split()
            if len(git_metadata) < 5:
                continue
            git_metadata[4] = git_metadata[4].strip('"')
            if strip_index is None:
                if os.path.splitext(os.path.basename(git_metadata[4]))[0].lower() == 'index':
                    git_metadata[4] = os.path.dirname(git_metadata[4])
            else:
                if git_metadata[4].endswith(strip_index):
                    for index_file_names in strip_index:
                        if git_metadata[4].endswith(index_file_names):
                            git_metadata[4] = git_metadata[4].removesuffix(index_file_names)
                            break
            git_metadata[4] = f'{git_metadata[4].strip("/")}/' if git_metadata[4].strip('/') else ''
            sitemap_file.write(f'''\
  <url>
    <loc>{url}/{html.escape(git_metadata[4])}</loc>
    <lastmod>{git_metadata[1]}T{git_metadata[2]}{git_metadata[3]}</lastmod>
    <changefreq>{calculate_crawl_frequency(git_metadata[1], repo_latest_iso_date)}</changefreq>
    <gh:sha>{git_metadata[0]}</gh:sha>
  </url>
''')
        sitemap_file.write('</urlset>')
    git_process.wait()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sitemap Generator')
    parser.add_argument('--url', help='Base URL')
    parser.add_argument('--include', nargs='+', help='File patterns to include in the sitemap (e.g., *.html)')
    parser.add_argument('--exclude', nargs='+', help='File patterns to exclude in the sitemap (e.g., 404.ht*)')
    parser.add_argument('--strip-index', nargs='+', help='Index filenames to strip for URL Canonicalization (e.g., index.html)')
    parsed_arguments = vars(parser.parse_args())
    filtered_function_args = {
        key: tuple(value) if isinstance(value, list) else value
        for key, value in parsed_arguments.items()
        if value is not None
    }
    generate_sitemap(**filtered_function_args)